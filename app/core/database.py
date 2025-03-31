import logging
from supabase import create_client, Client
from app.core.config import settings
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
)
def get_supabase_client() -> Client:
    """
    Create and return a Supabase client.
    Retries on connection failure with exponential backoff.
    """
    try:
        supabase: Client = create_client(
            settings.SUPABASE_URL, 
            settings.SUPABASE_KEY
        )
        logger.info("Supabase client created successfully")
        return supabase
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {str(e)}")
        raise

# Create a global Supabase client instance
supabase_client = get_supabase_client()