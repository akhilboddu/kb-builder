import logging
import uuid
from app.core.database import supabase_client
from app.models.chat import Message, MessageCreate, HandoverRequest, ConversationStatus
from datetime import datetime
from typing import Dict, Any, List, Callable, Optional
import asyncio

logger = logging.getLogger(__name__)

# Dictionary to store active channel subscriptions
_active_subscriptions = {}

async def subscribe_to_conversation(conversation_id: str, callback: Callable[[Dict[str, Any]], None]) -> str:
    """
    Subscribe to a conversation's realtime updates.
    
    Args:
        conversation_id: The ID of the conversation to subscribe to
        callback: Function to call when a message is received
        
    Returns:
        The subscription ID
    """
    try:
        channel_name = f"conversation:{conversation_id}"
        
        # Create subscription
        subscription = supabase_client.channel(channel_name)
        
        # Add listeners for messages
        subscription.on(
            "postgres_changes",
            event="INSERT",
            schema="public",
            table="messages",
            filter=f"conversation_id=eq.{conversation_id}",
            callback=lambda payload: callback(payload.new)
        )
        
        # Subscribe to the channel
        subscription.subscribe()
        
        # Store the subscription
        subscription_id = str(uuid.uuid4())
        _active_subscriptions[subscription_id] = subscription
        
        logger.info(f"Subscribed to conversation {conversation_id} with subscription ID {subscription_id}")
        return subscription_id
        
    except Exception as e:
        logger.error(f"Error subscribing to conversation: {str(e)}")
        raise

async def unsubscribe(subscription_id: str) -> bool:
    """
    Unsubscribe from a realtime subscription.
    
    Args:
        subscription_id: The ID of the subscription to remove
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if subscription_id in _active_subscriptions:
            subscription = _active_subscriptions[subscription_id]
            
            # Unsubscribe from the channel
            subscription.unsubscribe()
            
            # Remove from active subscriptions
            del _active_subscriptions[subscription_id]
            
            logger.info(f"Unsubscribed from subscription ID {subscription_id}")
            return True
        else:
            logger.warning(f"Subscription ID {subscription_id} not found")
            return False
    except Exception as e:
        logger.error(f"Error unsubscribing: {str(e)}")
        return False

async def broadcast_typing_indicator(conversation_id: str, is_typing: bool, user_id: str) -> bool:
    """
    Broadcast typing indicator to a conversation channel.
    
    Args:
        conversation_id: The ID of the conversation
        is_typing: Whether the user is typing
        user_id: The ID of the user who is typing
        
    Returns:
        True if successful, False otherwise
    """
    try:
        channel_name = f"conversation:{conversation_id}"
        
        # Broadcast typing event
        supabase_client.channel(channel_name).send({
            "type": "broadcast",
            "event": "typing",
            "payload": {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "is_typing": is_typing,
                "timestamp": datetime.now().isoformat()
            }
        })
        
        return True
    except Exception as e:
        logger.error(f"Error broadcasting typing indicator: {str(e)}")
        return False

async def save_message(message: MessageCreate) -> Message:
    """
    Save a message to the database and broadcast to the realtime channel.
    
    Args:
        message: The message to save
        
    Returns:
        The saved message with ID
    """
    try:
        message_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Prepare the message data
        message_data = {
            "id": message_id,
            "conversation_id": message.conversation_id,
            "sender_type": message.sender_type,
            "content": message.content,
            "timestamp": timestamp
        }
        
        # Add citations if provided
        if message.citations:
            message_data["citations"] = [citation.model_dump() for citation in message.citations]
            
        # Add confidence score if provided
        if message.confidence_score:
            message_data["confidence_score"] = message.confidence_score.model_dump()
        
        # Save to database
        response = supabase_client.table("messages").insert(message_data).execute()
        
        # Update conversation's updated_at timestamp
        supabase_client.table("conversations").update({
            "updated_at": timestamp
        }).eq("id", message.conversation_id).execute()
        
        # Create the message object
        saved_message = Message(
            id=message_id,
            conversation_id=message.conversation_id,
            sender_type=message.sender_type,
            content=message.content,
            timestamp=datetime.fromisoformat(timestamp),
            citations=message.citations,
            confidence_score=message.confidence_score
        )
        
        # Broadcast message to realtime channel (the insert trigger will handle this automatically)
        # But we can also explicitly broadcast an event for clients not using Postgres changes
        try:
            channel_name = f"conversation:{message.conversation_id}"
            supabase_client.channel(channel_name).send({
                "type": "broadcast",
                "event": "new_message",
                "payload": {
                    "message": message_data
                }
            })
        except Exception as e:
            # Log but don't fail the message save if broadcasting fails
            logger.warning(f"Failed to broadcast message: {str(e)}")
        
        return saved_message
    except Exception as e:
        logger.error(f"Error saving message: {str(e)}")
        raise

async def handle_handover(conversation_id: str, last_message_id: str, reason: str = "Low confidence") -> HandoverRequest:
    """
    Handle handover from bot to human agent.
    
    Args:
        conversation_id: The ID of the conversation
        last_message_id: The ID of the last message
        reason: The reason for the handover
        
    Returns:
        The created handover request
    """
    try:
        handover_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Create handover request
        handover_data = {
            "id": handover_id,
            "conversation_id": conversation_id,
            "last_message_id": last_message_id,
            "reason": reason,
            "created_at": timestamp,
            "status": "pending"
        }
        
        # Save to database
        response = supabase_client.table("handover_requests").insert(handover_data).execute()
        
        # Update conversation status to indicate handover is needed
        supabase_client.table("conversations").update({
            "status": ConversationStatus.OPEN.value,
            "updated_at": timestamp
        }).eq("id", conversation_id).execute()
        
        # Create a system message indicating handover
        system_message = MessageCreate(
            conversation_id=conversation_id,
            sender_type="bot",
            content="I'm connecting you with a human sales representative who can better assist you. Please wait a moment."
        )
        await save_message(system_message)
        
        # Return the handover request
        return HandoverRequest(
            conversation_id=conversation_id,
            last_message_id=last_message_id,
            reason=reason
        )
    except Exception as e:
        logger.error(f"Error handling handover: {str(e)}")
        raise

async def assign_conversation(conversation_id: str, agent_id: str) -> bool:
    """
    Assign a conversation to a human agent.
    
    Args:
        conversation_id: The ID of the conversation
        agent_id: The ID of the agent
        
    Returns:
        True if successful, False otherwise
    """
    try:
        timestamp = datetime.now().isoformat()
        
        # Update conversation assignment
        response = supabase_client.table("conversations").update({
            "status": ConversationStatus.ASSIGNED.value,
            "assigned_agent_id": agent_id,
            "updated_at": timestamp
        }).eq("id", conversation_id).execute()
        
        # Update any pending handover requests
        supabase_client.table("handover_requests").update({
            "status": "handled",
            "handled_by": agent_id
        }).eq("conversation_id", conversation_id).eq("status", "pending").execute()
        
        # Create a system message indicating agent assignment
        system_message = MessageCreate(
            conversation_id=conversation_id,
            sender_type="bot",
            content="A sales representative has joined the conversation and will assist you shortly."
        )
        await save_message(system_message)
        
        return True
    except Exception as e:
        logger.error(f"Error assigning conversation: {str(e)}")
        return False

async def close_conversation(conversation_id: str) -> bool:
    """
    Close a conversation.
    
    Args:
        conversation_id: The ID of the conversation
        
    Returns:
        True if successful, False otherwise
    """
    try:
        timestamp = datetime.now().isoformat()
        
        # Update conversation status
        response = supabase_client.table("conversations").update({
            "status": ConversationStatus.CLOSED.value,
            "updated_at": timestamp
        }).eq("id", conversation_id).execute()
        
        # Create a system message indicating conversation is closed
        system_message = MessageCreate(
            conversation_id=conversation_id,
            sender_type="bot",
            content="This conversation has been closed. Thank you for contacting us!"
        )
        await save_message(system_message)
        
        return True
    except Exception as e:
        logger.error(f"Error closing conversation: {str(e)}")
        return False