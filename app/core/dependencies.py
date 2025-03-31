import logging
from fastapi import Depends, HTTPException, Header, status
from app.core.database import supabase_client
from app.models.user import User, UserLimits
from typing import Optional

logger = logging.getLogger(__name__)

async def get_current_user(authorization: str = Header(...)) -> User:
    """
    Validate the JWT token in the Authorization header
    and return the current user information.
    
    The Authorization header should be in the format: Bearer <token>
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Verify the JWT token using Supabase
        user_response = supabase_client.auth.get_user(token)
        user_data = user_response.user
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user limits from database
        limits_response = supabase_client.table("user_limits").select("*").eq("user_id", user_data.id).execute()
        
        # Default limits if not found
        user_limits = UserLimits(
            max_bots=1,
            max_documents_per_kb=10,
            max_kb_per_bot=1
        )
        
        if limits_response.data:
            user_limits = UserLimits.model_validate(limits_response.data[0])
        
        # Return the user object with their limits
        return User(
            id=user_data.id,
            email=user_data.email,
            limits=user_limits
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def validate_bot_access(bot_id: str, user: User = Depends(get_current_user)) -> bool:
    """
    Validate if the current user has access to the specified bot.
    """
    try:
        # Check if the bot exists and belongs to the user
        bot_response = supabase_client.table("bots").select("*").eq("id", bot_id).eq("owner_id", user.id).execute()
        
        if not bot_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found or you don't have access to it"
            )
        
        return True
    except Exception as e:
        logger.error(f"Bot access validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate bot access"
        )