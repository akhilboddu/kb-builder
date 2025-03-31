import logging
from app.services.embedding_service import generate_embedding
from app.services.llm_service import generate_response
from app.core.database import supabase_client
from app.core.config import settings
from app.models.knowledge_base import SearchResult
from app.models.chat import ConfidenceScore
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

async def query_knowledge_base(bot_id: str, query: str, top_k: int = None) -> List[SearchResult]:
    """
    Retrieve the most relevant chunks from the knowledge base for a given query.
    
    Args:
        bot_id: The ID of the bot
        query: The user's query
        top_k: The number of chunks to retrieve (defaults to settings.DEFAULT_RETRIEVAL_COUNT)
        
    Returns:
        A list of SearchResult objects
    """
    if top_k is None:
        top_k = settings.DEFAULT_RETRIEVAL_COUNT
    
    try:
        # Generate an embedding for the query
        query_embedding = await generate_embedding(query)
        
        # Retrieve the knowledge base IDs for this bot
        kb_response = supabase_client.table("knowledge_bases").select("id").eq("bot_id", bot_id).execute()
        kb_ids = [kb["id"] for kb in kb_response.data]
        
        if not kb_ids:
            logger.warning(f"No knowledge bases found for bot {bot_id}")
            return []
        
        # Get document IDs for these knowledge bases
        doc_response = supabase_client.table("documents").select("id").in_("knowledge_base_id", kb_ids).eq("status", "completed").execute()
        doc_ids = [doc["id"] for doc in doc_response.data]
        
        if not doc_ids:
            logger.warning(f"No completed documents found for bot {bot_id}")
            return []
        
        # Perform vector similarity search using pgvector
        chunks_response = supabase_client.rpc(
            "match_document_chunks",
            {
                "query_embedding": query_embedding,
                "match_count": top_k,
                "document_ids": doc_ids
            }
        ).execute()
        
        # Process results
        results = []
        for chunk in chunks_response.data:
            results.append(SearchResult(
                text=chunk["content"],
                metadata=chunk["metadata"],
                score=chunk["similarity"]
            ))
        
        return results
    except Exception as e:
        logger.error(f"Error querying knowledge base: {str(e)}")
        raise

async def calculate_confidence_score(
    vector_similarity: float, 
    llm_confidence: float
) -> ConfidenceScore:
    """
    Calculate a combined confidence score based on vector similarity and LLM self-assessment.
    
    Args:
        vector_similarity: The similarity score from vector search (0-1)
        llm_confidence: The LLM's self-assessed confidence (0-1)
        
    Returns:
        A ConfidenceScore object
    """
    # Calculate the final score as a weighted average
    final_score = (vector_similarity * 0.5) + (llm_confidence * 0.5)
    
    return ConfidenceScore(
        vector_similarity=vector_similarity,
        llm_self_assessment=llm_confidence,
        final_score=final_score
    )

async def get_bot_settings(bot_id: str) -> Dict[str, Any]:
    """
    Retrieve bot settings from the database.
    
    Args:
        bot_id: The ID of the bot
        
    Returns:
        A dictionary of bot settings
    """
    try:
        response = supabase_client.table("bots").select("*").eq("id", bot_id).execute()
        
        if not response.data:
            raise ValueError(f"Bot with ID {bot_id} not found")
            
        bot_data = response.data[0]
        
        # Set default handover threshold if not present
        if "handover_threshold" not in bot_data or bot_data["handover_threshold"] is None:
            bot_data["handover_threshold"] = settings.DEFAULT_HANDOVER_THRESHOLD
            
        # Set default personality if not present
        if "personality" not in bot_data or not bot_data["personality"]:
            bot_data["personality"] = "A helpful, friendly AI sales assistant."
            
        return bot_data
    except Exception as e:
        logger.error(f"Error retrieving bot settings: {str(e)}")
        raise

async def get_conversation_history(conversation_id: str, max_messages: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve conversation history for the specified conversation.
    
    Args:
        conversation_id: The ID of the conversation
        max_messages: Maximum number of recent messages to retrieve
        
    Returns:
        A list of message dictionaries
    """
    try:
        response = supabase_client.table("messages") \
            .select("*") \
            .eq("conversation_id", conversation_id) \
            .order("timestamp", desc=True) \
            .limit(max_messages) \
            .execute()
            
        # Convert to chat format for LLM context
        messages = []
        for msg in sorted(response.data, key=lambda x: x["timestamp"]):
            role = "assistant" if msg["sender_type"] == "bot" else "user"
            messages.append({
                "role": role,
                "content": msg["content"]
            })
            
        return messages
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}")
        raise

async def query_bot(
    conversation_id: str, 
    query: str
) -> Tuple[str, List[Dict[str, Any]], ConfidenceScore, bool]:
    """
    Process a query to the bot and determine if handover is needed.
    
    Args:
        conversation_id: The ID of the conversation
        query: The user's query
        
    Returns:
        Tuple of (response text, citations, confidence score, needs_handover)
    """
    try:
        # Get conversation details
        conv_response = supabase_client.table("conversations").select("*").eq("id", conversation_id).execute()
        
        if not conv_response.data:
            raise ValueError(f"Conversation with ID {conversation_id} not found")
            
        conversation = conv_response.data[0]
        bot_id = conversation["bot_id"]
        
        # Get bot settings
        bot_settings = await get_bot_settings(bot_id)
        handover_threshold = bot_settings.get("handover_threshold", settings.DEFAULT_HANDOVER_THRESHOLD)
        personality = bot_settings.get("personality", "A helpful, friendly AI sales assistant.")
        
        # Get conversation history
        history = await get_conversation_history(conversation_id)
        
        # Query the knowledge base
        search_results = await query_knowledge_base(bot_id, query)
        
        # If no results found, handle gracefully
        if not search_results:
            logger.warning(f"No results found for query: {query}")
            # Generate a response indicating no information was found
            response = {
                "response": "I don't have specific information to answer that question. Would you like me to connect you with a human sales representative who can help you?",
                "citations": [],
                "llm_confidence": 0.1
            }
            confidence = await calculate_confidence_score(0.0, 0.1)
            return response["response"], response["citations"], confidence, True
        
        # Calculate average vector similarity for the top results
        avg_similarity = sum(result.score for result in search_results) / len(search_results)
        
        # Generate response using LLM
        response = await generate_response(
            query=query,
            context_chunks=search_results,
            bot_personality=personality,
            conversation_history=history
        )
        
        # Calculate confidence score
        confidence = await calculate_confidence_score(
            vector_similarity=avg_similarity,
            llm_confidence=response["llm_confidence"]
        )
        
        # Determine if handover is needed
        needs_handover = confidence.final_score < handover_threshold
        
        return response["response"], response["citations"], confidence, needs_handover
    except Exception as e:
        logger.error(f"Error querying bot: {str(e)}")
        raise