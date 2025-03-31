from pydantic import BaseModel, EmailStr
from typing import Optional

class UserLimits(BaseModel):
    """User subscription limits"""
    max_bots: int
    max_documents_per_kb: int
    max_kb_per_bot: int
    
class User(BaseModel):
    """User model"""
    id: str
    email: EmailStr
    limits: Optional[UserLimits] = None