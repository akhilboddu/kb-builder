"""
Data models for document processing.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from sqlalchemy import Column, String, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class DocumentResponse(BaseModel):
    """Response model for document operations."""
    document_id: str = Field(..., description="Document ID")
    status: str = Field(..., description="Status of the document processing")
    message: str = Field(..., description="Descriptive message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc-fbd8a034-8d9e-4a93-b814-b3a3f3e5f254",
                "status": "processing",
                "message": "Document processing started"
            }
        }


class DocumentBase(BaseModel):
    """Base document model."""
    document_id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    filename: str = Field(..., description="Original filename")
    category: Optional[str] = Field(None, description="Document category")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    page_count: int = Field(..., description="Number of pages")
    chunk_count: int = Field(..., description="Number of chunks created")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    processing_status: str = Field(..., description="Processing status")

    class Config:
        from_attributes = True


class DocumentDB(Base):
    """Document database model."""
    __tablename__ = "documents"

    document_id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tags: Mapped[List[str]] = mapped_column(JSON, nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processing_status: Mapped[str] = mapped_column(String, nullable=False)


class DocumentInfo(DocumentBase):
    """Document information model."""
    pass


class DocumentChunk(BaseModel):
    """Model for document chunks."""
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Chunk ID")
    document_id: str = Field(..., description="Parent document ID")
    content: str = Field(..., description="Chunk content")
    page_number: Optional[int] = Field(None, description="Source page number")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata") 