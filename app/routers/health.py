from fastapi import APIRouter, HTTPException, status
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify the API is running.
    For testing purposes only - does not check external services.
    """
    return {
        "status": "healthy",
        "message": "API is running"
    }