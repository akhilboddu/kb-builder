from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal, Any
from datetime import datetime
from enum import Enum

class ConversationStatus(str, Enum):
    """Conversation status"""
    OPEN = "open"
    ASSIGNED = "assigned"
    CLOSED = "closed"

class SenderType(str, Enum):
    """Message sender type"""
    USER = "user"
    BOT = "bot"
    HUMAN_AGENT = "human_agent"

class SourceCitation(BaseModel):
    """Source citation for bot responses"""
    text: str
    source_url: Optional[str] = None
    title: str
    
class ConfidenceScore(BaseModel):
    """Confidence score details"""
    vector_similarity: float = Field(ge=0, le=1)
    llm_self_assessment: float = Field(ge=0, le=1)
    final_score: float = Field(ge=0, le=1)
    
class Message(BaseModel):
    """Chat message model"""
    id: str
    conversation_id: str
    sender_type: SenderType
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    citations: Optional[List[SourceCitation]] = None
    confidence_score: Optional[ConfidenceScore] = None
    
class MessageCreate(BaseModel):
    """Message creation request"""
    conversation_id: str
    sender_type: SenderType
    content: str
    citations: Optional[List[SourceCitation]] = None
    confidence_score: Optional[ConfidenceScore] = None
    
class Conversation(BaseModel):
    """Conversation model"""
    id: str
    bot_id: str
    status: ConversationStatus = ConversationStatus.OPEN
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    assigned_agent_id: Optional[str] = None
    
class ConversationCreate(BaseModel):
    """Conversation creation request"""
    bot_id: str
    
class HandoverRequest(BaseModel):
    """Handover request model"""
    conversation_id: str
    last_message_id: str
    reason: str
    
class AgentAvailability(BaseModel):
    """Agent availability status"""
    agent_id: str
    status: Literal["available", "busy", "offline"]
    last_updated: datetime