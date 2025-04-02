"""Document processing service."""
import logging
import uuid
from datetime import datetime
from typing import List, Optional, BinaryIO
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.document_repository import (
    save_document,
    get_document,
    get_documents,
    update_document,
    delete_document
)
from app.db.vector_store import (
    add_chunks_to_vector_store,
    get_chunks_by_document_id,
    search_vector_store
)
from app.models.document import DocumentInfo, DocumentResponse
from app.utils.pdf import extract_text_from_pdf, split_text_into_chunks

# Initialize logger
logger = logging.getLogger(__name__)

def parse_tags(tags_str: Optional[str] = None) -> List[str]:
    """Parse comma-separated tags string into a list."""
    if not tags_str:
        return []
    return [tag.strip() for tag in tags_str.split(',') if tag.strip()]

async def process_pdf(
    file: UploadFile,
    title: str,
    category: Optional[str] = None,
    tags: Optional[str] = None,
    session: AsyncSession = None
) -> DocumentResponse:
    """
    Process a PDF file and store its information.
    
    Args:
        file: PDF file to process
        title: Document title
        category: Optional document category
        tags: Optional document tags
        session: Database session
        
    Returns:
        DocumentResponse with document ID and status
    """
    try:
        # Read file content
        content = await file.read()
        
        # Extract text from PDF
        pages, total_pages = extract_text_from_pdf(content)
        
        if not pages:
            raise ValueError("No text content found in PDF")
        
        # Create document chunks
        chunks = []
        for page_text in pages:
            chunks.extend(split_text_into_chunks(page_text))
            
        # Create document info
        doc_info = DocumentInfo(
            document_id=str(uuid.uuid4()),
            title=title,
            filename=file.filename,
            category=category,
            tags=parse_tags(tags),
            page_count=total_pages,
            chunk_count=len(chunks),
            created_at=datetime.now(),
            processing_status="completed"  # Changed from "processing" since we're done
        )
        
        # Save document
        await save_document(doc_info, session)
        
        return DocumentResponse(
            document_id=doc_info.document_id,
            status="success",
            message="Document processed successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to process document: {str(e)}")
        raise ValueError(str(e))

async def get_document_info(
    document_id: str,
    session: AsyncSession
) -> Optional[DocumentInfo]:
    """
    Get document information.
    
    Args:
        document_id: Document ID
        session: Database session
        
    Returns:
        DocumentInfo if found, None otherwise
    """
    try:
        return await get_document(document_id, session)
        
    except Exception as e:
        logger.error(f"Failed to get document: {str(e)}")
        raise ValueError(str(e))

async def get_documents_info(
    session: AsyncSession,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> List[DocumentInfo]:
    """
    Get documents with optional filters.
    
    Args:
        session: Database session
        category: Optional category filter
        tags: Optional tag filters
        
    Returns:
        List of DocumentInfo objects
    """
    try:
        return await get_documents(session, category, tags)
        
    except Exception as e:
        logger.error(f"Failed to get documents: {str(e)}")
        raise ValueError(str(e))

async def delete_document_info(
    document_id: str,
    session: AsyncSession
) -> None:
    """
    Delete a document.
    
    Args:
        document_id: Document ID to delete
        session: Database session
    """
    try:
        await delete_document(document_id, session)
        
    except Exception as e:
        logger.error(f"Failed to delete document: {str(e)}")
        raise ValueError(str(e))

async def get_document_chunks(
    document_id: str,
    session: AsyncSession
) -> List[str]:
    """
    Get document chunks.
    
    Args:
        document_id: Document ID
        session: Database session
        
    Returns:
        List of document chunks
    """
    try:
        # Get document
        document = await get_document(document_id, session)
        if not document:
            raise ValueError(f"Document {document_id} not found")
            
        # Read file content
        with open(document.filename, 'rb') as f:
            content = f.read()
            
        # Extract text and create chunks
        pages = extract_text_from_pdf(content)
        chunks = []
        for page in pages:
            chunks.extend(split_text_into_chunks(page))
            
        return chunks
        
    except Exception as e:
        logger.error(f"Failed to get document chunks: {str(e)}")
        raise ValueError(str(e))

async def update_document_info(document: DocumentInfo, session: AsyncSession) -> DocumentInfo:
    """Update document."""
    try:
        doc_db = await update_document(document, session)
        return DocumentInfo.model_validate(doc_db)
    except ValueError as e:
        logger.error(f"Document not found: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to update document: {str(e)}")
        raise ValueError(f"Failed to update document: {str(e)}")

async def search_documents(query: str, filters: Optional[dict] = None) -> List[dict]:
    """Search documents."""
    try:
        return await search_vector_store(query, filters)
    except Exception as e:
        logger.error(f"Failed to search documents: {str(e)}")
        raise ValueError(f"Failed to search documents: {str(e)}")

__all__ = [
    'process_pdf',
    'get_document_info',
    'get_documents_info',
    'delete_document_info',
    'get_document_chunks',
    'update_document_info',
    'search_documents'
]