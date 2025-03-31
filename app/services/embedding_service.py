import logging
import openai
from app.core.config import settings
from typing import List
from ratelimit import limits, sleep_and_retry
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Rate limit: 1 request per second, with flexibility (sleep if exceeded)
ONE_SECOND = 1

@sleep_and_retry
@limits(calls=20, period=ONE_SECOND*60)
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
)
async def generate_embedding(text: str) -> List[float]:
    """
    Generate an embedding for the given text using OpenAI's embeddings API.
    
    Args:
        text: The text to generate an embedding for
        
    Returns:
        A list of floats representing the embedding vector
    """
    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.embeddings.create(
            input=text,
            model=settings.EMBEDDING_MODEL
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise

@sleep_and_retry
@limits(calls=20, period=ONE_SECOND*60)
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
)
async def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a batch of texts.
    
    Args:
        texts: List of texts to generate embeddings for
        
    Returns:
        A list of embedding vectors
    """
    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.embeddings.create(
            input=texts,
            model=settings.EMBEDDING_MODEL
        )
        return [data.embedding for data in response.data]
    except Exception as e:
        logger.error(f"Error generating batch embeddings: {str(e)}")
        raise