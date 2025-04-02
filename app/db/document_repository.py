"""
Repository for document metadata storage.
"""
import logging
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from sqlalchemy import Column, String, Integer, DateTime, Text, select, delete, or_, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.sql import text

from app.models.document import DocumentDB, DocumentInfo

# Setup logging
logger = logging.getLogger(__name__)

# Create SQLite engine
DB_DIR = "./data/db"
os.makedirs(DB_DIR, exist_ok=True)
DATABASE_URL = f"sqlite+aiosqlite:///{DB_DIR}/documents.db"
engine = create_async_engine(DATABASE_URL)

# Create declarative base
Base = declarative_base()

# Define Document model
class DocumentRecord(Base):
    """SQLAlchemy model for document records."""
    __tablename__ = "documents"
    
    document_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    category = Column(String, nullable=True)
    tags = Column(Text, nullable=False)  # Stored as JSON
    page_count = Column(Integer, nullable=False)
    chunk_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    processing_status = Column(String, nullable=False)
    
    def to_document_info(self) -> DocumentInfo:
        """Convert to Pydantic model."""
        return DocumentInfo(
            document_id=self.document_id,
            title=self.title,
            filename=self.filename,
            category=self.category,
            tags=json.loads(self.tags),
            page_count=self.page_count,
            chunk_count=self.chunk_count,
            created_at=self.created_at,
            processing_status=self.processing_status
        )

# Create tables
async def create_tables():
    """Create database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Remove the direct asyncio.run call that causes issues with uvicorn
# import asyncio
# asyncio.run(create_tables())

async def save_document(document: DocumentInfo, session: AsyncSession) -> None:
    """Save document to database."""
    try:
        db_document = DocumentDB(
            document_id=document.document_id,
            title=document.title,
            filename=document.filename,
            category=document.category,
            tags=document.tags,
            page_count=document.page_count,
            chunk_count=document.chunk_count,
            created_at=document.created_at,
            processing_status=document.processing_status
        )
        session.add(db_document)
        await session.commit()
        
    except Exception as e:
        logger.error(f"Error saving document: {str(e)}")
        await session.rollback()
        raise ValueError(f"Failed to save document: {str(e)}")

async def get_document(document_id: str, session: AsyncSession) -> Optional[DocumentInfo]:
    """Get document by ID."""
    try:
        result = await session.execute(
            select(DocumentDB).where(DocumentDB.document_id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if document:
            return DocumentInfo(
                document_id=document.document_id,
                title=document.title,
                filename=document.filename,
                category=document.category,
                tags=document.tags,
                page_count=document.page_count,
                chunk_count=document.chunk_count,
                created_at=document.created_at,
                processing_status=document.processing_status
            )
        return None
        
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        raise ValueError(f"Failed to get document: {str(e)}")

async def get_documents(
    session: AsyncSession,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> List[DocumentInfo]:
    """Get documents with optional filters."""
    try:
        # Start with base query
        query = select(DocumentDB)
        
        # Build filter conditions
        conditions = []
        
        # Add category filter if provided
        if category:
            conditions.append(DocumentDB.category == category)
            
        # Add tag filters if provided
        if tags:
            for tag in tags:
                conditions.append(
                    text("EXISTS (SELECT 1 FROM json_each(documents.tags) WHERE value = :tag)").bindparams(tag=tag)
                )
        
        # Apply all conditions if any exist
        if conditions:
            query = query.where(and_(*conditions))
            
        # Execute query
        result = await session.execute(query)
        documents = result.scalars().all()
        
        # Convert to DocumentInfo objects
        return [
            DocumentInfo(
                document_id=doc.document_id,
                title=doc.title,
                filename=doc.filename,
                category=doc.category,
                tags=doc.tags,
                page_count=doc.page_count,
                chunk_count=doc.chunk_count,
                created_at=doc.created_at,
                processing_status=doc.processing_status
            )
            for doc in documents
        ]
        
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        raise ValueError(f"Failed to get documents: {str(e)}")

async def update_document(document: DocumentInfo, session: AsyncSession) -> None:
    """Update document in database."""
    try:
        result = await session.execute(
            select(DocumentDB).where(DocumentDB.document_id == document.document_id)
        )
        db_document = result.scalar_one_or_none()
        
        if not db_document:
            raise ValueError(f"Document {document.document_id} not found")
            
        # Update fields
        db_document.title = document.title
        db_document.filename = document.filename
        db_document.category = document.category
        db_document.tags = document.tags
        db_document.page_count = document.page_count
        db_document.chunk_count = document.chunk_count
        db_document.processing_status = document.processing_status
        
        await session.commit()
        
    except Exception as e:
        logger.error(f"Error updating document: {str(e)}")
        await session.rollback()
        raise ValueError(f"Failed to update document: {str(e)}")

async def delete_document(document_id: str, session: AsyncSession) -> None:
    """Delete document from database."""
    try:
        # Check if document exists
        result = await session.execute(
            select(DocumentDB).where(DocumentDB.document_id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise ValueError(f"Document {document_id} not found")
            
        # Delete document
        await session.execute(
            text("DELETE FROM documents WHERE document_id = :id").bindparams(id=document_id)
        )
        await session.commit()
        
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        await session.rollback()
        raise ValueError(f"Failed to delete document: {str(e)}")

__all__ = [
    'save_document',
    'get_document',
    'get_documents',
    'update_document',
    'delete_document'
] 