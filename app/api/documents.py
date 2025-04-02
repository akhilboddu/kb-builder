"""Document API endpoints."""
import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import DocumentResponse, DocumentInfo
from app.services.document_service import (
    process_pdf,
    get_document_info,
    get_documents_info,
    delete_document_info,
    get_document_chunks
)
from app.db.session import get_db

router = APIRouter(prefix="/api/documents", tags=["Documents"])

# Initialize logger
logger = logging.getLogger(__name__)

def parse_tags(tags_str: Optional[str] = None) -> List[str]:
    """Parse comma-separated tags string into a list."""
    if not tags_str:
        return []
    return [tag.strip() for tag in tags_str.split(',') if tag.strip()]

@router.post("/upload-pdf", response_model=DocumentResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    title: str = Form(...),
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and process a PDF document.
    
    Args:
        file: The PDF file to upload
        title: Document title
        category: Optional document category
        tags: Optional comma-separated tags
        db: Database session
        
    Returns:
        DocumentResponse with document ID and status
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="File must be a PDF"
            )
        
        # Process PDF
        response = await process_pdf(
            file=file,
            title=title,
            category=category,
            tags=tags,
            session=db
        )
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        await file.close()

@router.get("/", response_model=List[DocumentInfo])
async def list_documents(
    category: Optional[str] = None,
    tags: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List documents with optional filters.
    
    Args:
        category: Optional category filter
        tags: Optional comma-separated tags filter
        db: Database session
        
    Returns:
        List of DocumentInfo objects
    """
    try:
        # Get documents
        documents = await get_documents_info(
            session=db,
            category=category,
            tags=parse_tags(tags)
        )
        return documents
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific document by ID.
    
    Args:
        document_id: Document ID to retrieve
        db: Database session
        
    Returns:
        DocumentInfo object
    """
    try:
        document = await get_document_info(document_id, db)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document by ID.
    
    Args:
        document_id: Document ID to delete
        db: Database session
        
    Returns:
        Success message
    """
    try:
        await delete_document_info(document_id, db)
        return {"message": f"Document {document_id} deleted successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{document_id}/chunks")
async def get_chunks(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get chunks for a document.
    
    Args:
        document_id: Document ID to get chunks for
        db: Database session
        
    Returns:
        List of document chunks
    """
    try:
        chunks = await get_document_chunks(document_id, db)
        return chunks
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting document chunks: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")