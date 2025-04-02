from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum

class DocumentStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"

class HeadingItem(BaseModel):
    """Heading item from web scraper output"""
    text: str
    level: int
    id: str = Field(description="Unique identifier for the heading")

class ParagraphItem(BaseModel):
    """Paragraph item from web scraper output"""
    text: str
    id: str = Field(description="Unique identifier for the paragraph")

class LinkItem(BaseModel):
    """Link item from web scraper output"""
    text: str
    url: HttpUrl
    id: str = Field(description="Unique identifier for the link")

class WebpageData(BaseModel):
    """Webpage data from web scraper"""
    url: HttpUrl
    title: str
    headings: List[HeadingItem]
    paragraphs: List[ParagraphItem]
    links: List[LinkItem]

class DocumentChunk(BaseModel):
    """Document chunk with text content and metadata"""
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentMetadata(BaseModel):
    """Document metadata"""
    source_url: Optional[HttpUrl] = None
    title: str
    filetype: str
    created_at: datetime = Field(default_factory=datetime.now)
    chunk_count: Optional[int] = None
    
class KnowledgeBase(BaseModel):
    """Knowledge base model"""
    id: str
    bot_id: str
    name: str
    created_at: datetime = Field(default_factory=datetime.now)
    
class KnowledgeBaseCreate(BaseModel):
    """Knowledge base creation request"""
    name: str
    bot_id: str
    
class Document(BaseModel):
    """Document model"""
    id: str
    knowledge_base_id: str
    title: str
    status: DocumentStatus = DocumentStatus.PENDING
    metadata: DocumentMetadata
    created_at: datetime = Field(default_factory=datetime.now)
    
class DocumentCreate(BaseModel):
    """Document creation request"""
    knowledge_base_id: str
    title: str
    source_url: Optional[HttpUrl] = None
    
class SearchRequest(BaseModel):
    """Request model for search operations."""
    query: str
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None

class SearchResult(BaseModel):
    """Search result model"""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float
    source: Optional[str] = None

class SearchResponse(BaseModel):
    """Search response model"""
    query: str
    results: List[SearchResult]
    count: int

class KnowledgeBaseStats(BaseModel):
    """Knowledge base statistics model"""
    total_documents: int = 0
    total_entries: int = 0
    total_pages: int = 0
    total_chunks: int = 0
    by_source: Dict[str, int] = Field(default_factory=dict)
    by_category: Dict[str, int] = Field(default_factory=dict)
    knowledge_bases: Dict[str, int] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)

class ReindexResponse(BaseModel):
    """Response model for reindex operation"""
    status: str
    message: str