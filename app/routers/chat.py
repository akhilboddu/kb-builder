import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Dict, Any, Optional
from app.models.chat import (
    Conversation, ConversationCreate, Message, MessageCreate,
    SenderType, ConversationStatus, HandoverRequest
)
from app.models.user import User
from app.core.dependencies import get_current_user, validate_bot_access
from app.core.database import supabase_client
from app.services.rag_service import query_bot
from app.services.realtime_service import save_message, handle_handover, assign_conversation, close_conversation, broadcast_typing_indicator
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/conversations", response_model=Conversation)
async def create_conversation(
    conversation_data: ConversationCreate,
    user: User = Depends(get_current_user)
):
    """
    Create a new conversation with a bot.
    """
    try:
        # Verify bot access
        await validate_bot_access(conversation_data.bot_id, user)
        
        # Create conversation
        conversation_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        conversation_dict = {
            "id": conversation_id,
            "bot_id": conversation_data.bot_id,
            "status": ConversationStatus.OPEN.value,
            "created_at": timestamp,
            "updated_at": timestamp
        }
        
        response = supabase_client.table("conversations").insert(conversation_dict).execute()
        
        # Return the created conversation
        return Conversation(
            id=conversation_id,
            bot_id=conversation_data.bot_id,
            status=ConversationStatus.OPEN,
            created_at=datetime.fromisoformat(timestamp),
            updated_at=datetime.fromisoformat(timestamp)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation"
        )

@router.get("/conversations/{bot_id}", response_model=List[Conversation])
async def list_conversations(
    bot_id: str,
    user: User = Depends(get_current_user)
):
    """
    List all conversations for a bot.
    """
    try:
        # Verify bot access
        await validate_bot_access(bot_id, user)
        
        # Get conversations
        response = supabase_client.table("conversations").select("*").eq("bot_id", bot_id).execute()
        
        # Convert to model
        conversations = []
        for conv_data in response.data:
            conversations.append(Conversation(
                id=conv_data["id"],
                bot_id=conv_data["bot_id"],
                status=ConversationStatus(conv_data["status"]),
                created_at=datetime.fromisoformat(conv_data["created_at"]),
                updated_at=datetime.fromisoformat(conv_data["updated_at"]),
                assigned_agent_id=conv_data.get("assigned_agent_id")
            ))
            
        return conversations
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversations"
        )

@router.post("/messages", response_model=Message)
async def create_message(
    message_data: MessageCreate,
    user: User = Depends(get_current_user)
):
    """
    Send a message in a conversation.
    """
    try:
        # Get conversation to verify access
        conv_response = supabase_client.table("conversations").select("*").eq("id", message_data.conversation_id).execute()
        
        if not conv_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
            
        conversation = conv_response.data[0]
        bot_id = conversation["bot_id"]
        
        # Verify bot access
        await validate_bot_access(bot_id, user)
        
        # Check if conversation is closed
        if conversation["status"] == ConversationStatus.CLOSED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot send message to a closed conversation"
            )
            
        # Save the message
        saved_message = await save_message(message_data)
        
        return saved_message
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create message"
        )

@router.get("/messages/{conversation_id}", response_model=List[Message])
async def get_messages(
    conversation_id: str,
    limit: int = 50,
    user: User = Depends(get_current_user)
):
    """
    Get messages from a conversation.
    """
    try:
        # Get conversation to verify access
        conv_response = supabase_client.table("conversations").select("*").eq("id", conversation_id).execute()
        
        if not conv_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
            
        conversation = conv_response.data[0]
        bot_id = conversation["bot_id"]
        
        # Verify bot access
        await validate_bot_access(bot_id, user)
        
        # Get messages
        response = supabase_client.table("messages").select("*").eq("conversation_id", conversation_id).order("timestamp").limit(limit).execute()
        
        # Convert to model
        messages = []
        for msg_data in response.data:
            message = Message(
                id=msg_data["id"],
                conversation_id=msg_data["conversation_id"],
                sender_type=SenderType(msg_data["sender_type"]),
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
            )
            
            # Add citations if present
            if msg_data.get("citations"):
                message.citations = msg_data["citations"]
                
            # Add confidence score if present
            if msg_data.get("confidence_score"):
                message.confidence_score = msg_data["confidence_score"]
                
            messages.append(message)
            
        return messages
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get messages"
        )

@router.post("/query", response_model=Message)
async def query_conversation(
    conversation_id: str,
    query: str,
    user: User = Depends(get_current_user)
):
    """
    Send a query to the bot and get a response.
    """
    try:
        # Get conversation to verify access
        conv_response = supabase_client.table("conversations").select("*").eq("id", conversation_id).execute()
        
        if not conv_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
            
        conversation = conv_response.data[0]
        bot_id = conversation["bot_id"]
        
        # Verify bot access
        await validate_bot_access(bot_id, user)
        
        # Check if conversation is closed or assigned to an agent
        if conversation["status"] == ConversationStatus.CLOSED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot query a closed conversation"
            )
            
        if conversation["status"] == ConversationStatus.ASSIGNED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conversation is currently assigned to a human agent"
            )
            
        # Save the user message
        user_message = MessageCreate(
            conversation_id=conversation_id,
            sender_type=SenderType.USER,
            content=query
        )
        saved_user_message = await save_message(user_message)
        
        # Query the bot
        response_text, citations, confidence_score, needs_handover = await query_bot(
            conversation_id=conversation_id,
            query=query
        )
        
        # Save the bot response
        bot_message = MessageCreate(
            conversation_id=conversation_id,
            sender_type=SenderType.BOT,
            content=response_text,
            citations=citations,
            confidence_score=confidence_score
        )
        saved_bot_message = await save_message(bot_message)
        
        # Handle handover if needed
        if needs_handover:
            await handle_handover(
                conversation_id=conversation_id,
                last_message_id=saved_bot_message.id,
                reason=f"Low confidence score: {confidence_score.final_score:.2f}"
            )
        
        return saved_bot_message
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query conversation"
        )

@router.post("/handover", response_model=HandoverRequest)
async def request_handover(
    conversation_id: str,
    reason: str = "User requested handover",
    user: User = Depends(get_current_user)
):
    """
    Request a handover from bot to human agent.
    """
    try:
        # Get conversation to verify access
        conv_response = supabase_client.table("conversations").select("*").eq("id", conversation_id).execute()
        
        if not conv_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
            
        conversation = conv_response.data[0]
        bot_id = conversation["bot_id"]
        
        # Verify bot access
        await validate_bot_access(bot_id, user)
        
        # Check if conversation is already assigned or closed
        if conversation["status"] == ConversationStatus.ASSIGNED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conversation is already assigned to a human agent"
            )
            
        if conversation["status"] == ConversationStatus.CLOSED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot request handover for a closed conversation"
            )
            
        # Get the last message
        last_message_response = supabase_client.table("messages").select("*").eq("conversation_id", conversation_id).order("timestamp", desc=True).limit(1).execute()
        
        if not last_message_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No messages found in conversation"
            )
            
        last_message_id = last_message_response.data[0]["id"]
        
        # Handle the handover
        handover_request = await handle_handover(
            conversation_id=conversation_id,
            last_message_id=last_message_id,
            reason=reason
        )
        
        return handover_request
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting handover: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to request handover"
        )

@router.post("/assign")
async def assign_agent(
    conversation_id: str,
    agent_id: str,
    user: User = Depends(get_current_user)
):
    """
    Assign a conversation to a human agent.
    """
    try:
        # Get conversation to verify access
        conv_response = supabase_client.table("conversations").select("*").eq("id", conversation_id).execute()
        
        if not conv_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
            
        conversation = conv_response.data[0]
        bot_id = conversation["bot_id"]
        
        # Verify bot access
        await validate_bot_access(bot_id, user)
        
        # Check if conversation is closed
        if conversation["status"] == ConversationStatus.CLOSED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign a closed conversation"
            )
            
        # Assign the conversation
        success = await assign_conversation(
            conversation_id=conversation_id,
            agent_id=agent_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign conversation"
            )
            
        return {"status": "success", "message": "Conversation assigned successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign conversation"
        )

@router.post("/close")
async def close_conversation_endpoint(
    conversation_id: str,
    user: User = Depends(get_current_user)
):
    """
    Close a conversation.
    """
    try:
        # Get conversation to verify access
        conv_response = supabase_client.table("conversations").select("*").eq("id", conversation_id).execute()
        
        if not conv_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
            
        conversation = conv_response.data[0]
        bot_id = conversation["bot_id"]
        
        # Verify bot access
        await validate_bot_access(bot_id, user)
        
        # Check if conversation is already closed
        if conversation["status"] == ConversationStatus.CLOSED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conversation is already closed"
            )
            
        # Close the conversation
        success = await close_conversation(conversation_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to close conversation"
            )
            
        return {"status": "success", "message": "Conversation closed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to close conversation"
        )

@router.post("/subscribe")
async def subscribe_to_conversation_endpoint(
    conversation_id: str,
    callback_url: str,
    user: User = Depends(get_current_user)
):
    """
    Create a subscription to receive realtime updates for a conversation.
    
    The callback_url is used to identify the client-side callback that will handle 
    the realtime events. The actual callback handling must be implemented on the client.
    """
    try:
        # Get conversation to verify access
        conv_response = supabase_client.table("conversations").select("*").eq("id", conversation_id).execute()
        
        if not conv_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
            
        conversation = conv_response.data[0]
        bot_id = conversation["bot_id"]
        
        # Verify bot access
        await validate_bot_access(bot_id, user)
        
        # Return subscription info
        return {
            "conversation_id": conversation_id,
            "channel": f"conversation:{conversation_id}",
            "subscription_info": {
                "schema": "public",
                "table": "messages",
                "filter": f"conversation_id=eq.{conversation_id}"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription"
        )

@router.post("/typing")
async def send_typing_indicator(
    conversation_id: str,
    is_typing: bool,
    user: User = Depends(get_current_user)
):
    """
    Send a typing indicator for a conversation.
    """
    try:
        # Get conversation to verify access
        conv_response = supabase_client.table("conversations").select("*").eq("id", conversation_id).execute()
        
        if not conv_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
            
        conversation = conv_response.data[0]
        bot_id = conversation["bot_id"]
        
        # Verify bot access
        await validate_bot_access(bot_id, user)
        
        # Check if conversation is closed
        if conversation["status"] == ConversationStatus.CLOSED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot send typing indicator to a closed conversation"
            )
            
        # Send typing indicator
        success = await broadcast_typing_indicator(conversation_id, is_typing, user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send typing indicator"
            )
            
        return {"status": "success", "is_typing": is_typing}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending typing indicator: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send typing indicator"
        )