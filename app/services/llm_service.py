import logging
import openai
from ratelimit import limits, sleep_and_retry
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.models.knowledge_base import SearchResult
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Rate limit: 10 requests per minute
ONE_MINUTE = 60

@sleep_and_retry
@limits(calls=10, period=ONE_MINUTE)
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
)
async def generate_response(
    query: str, 
    context_chunks: List[SearchResult], 
    bot_personality: str,
    conversation_history: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a response using the LLM based on the query and retrieved context.
    
    Args:
        query: The user's query
        context_chunks: The retrieved context chunks
        bot_personality: The bot's personality description
        conversation_history: Previous conversation history (optional)
        
    Returns:
        A dictionary containing the response and source citations
    """
    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Format the context for the prompt
        formatted_context = ""
        for i, chunk in enumerate(context_chunks):
            formatted_context += f"[Document {i+1}]: {chunk.text}\nSource: {chunk.metadata.get('title', 'Unknown')}, URL: {chunk.metadata.get('source_url', 'None')}\n\n"
        
        # Format conversation history if provided
        conversation_context = ""
        if conversation_history:
            conversation_context = "Previous conversation:\n"
            for msg in conversation_history:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                conversation_context += f"{role.capitalize()}: {content}\n"
            conversation_context += "\n"
        
        # Build the messages for the chat
        messages = [
            {
                "role": "system", 
                "content": f"""You are an AI sales agent with the following personality: {bot_personality}
                
Your task is to respond to the user's query using ONLY the information provided in the context below.
If the context doesn't contain the answer, admit that you don't know rather than making up an answer.

When referencing information from the context, cite your sources using [Document X] notation.

{conversation_context}

Context:
{formatted_context}
"""
            },
            {"role": "user", "content": query}
        ]
        
        # Add a final instruction to assess confidence
        messages.append({
            "role": "user",
            "content": """After you've answered my question, please add a separate paragraph with an honest assessment 
of your confidence in the answer on a scale from 0 to 1, where 0 means completely unsure and 1 means absolutely confident.
Format it exactly like this on its own line: "CONFIDENCE_SCORE: X.XX"
"""
        })
        
        # Generate the response
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
        )
        
        response_text = response.choices[0].message.content
        
        # Extract the confidence score
        confidence_score = 0.5  # Default value
        if "CONFIDENCE_SCORE:" in response_text:
            try:
                # Extract and parse the confidence score
                score_text = response_text.split("CONFIDENCE_SCORE:")[1].strip().split()[0]
                confidence_score = float(score_text)
                
                # Remove the confidence score line from the response
                response_text = response_text.split("CONFIDENCE_SCORE:")[0].strip()
            except Exception as e:
                logger.warning(f"Failed to extract confidence score: {str(e)}")
        
        # Extract citations
        citations = []
        for i, chunk in enumerate(context_chunks):
            doc_id = f"Document {i+1}"
            if doc_id in response_text:
                citations.append({
                    "text": chunk.text[:100] + "...",  # First 100 chars of the chunk
                    "source_url": chunk.metadata.get("source_url"),
                    "title": chunk.metadata.get("title", "Unknown Source")
                })
        
        return {
            "response": response_text,
            "citations": citations,
            "llm_confidence": confidence_score
        }
    except Exception as e:
        logger.error(f"Error generating LLM response: {str(e)}")
        raise