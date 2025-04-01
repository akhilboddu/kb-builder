"""
API routes for document (PDF) processing.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query, Path, Form, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import DocumentResponse, DocumentInfo
# Import both document service implementations
from app.services.document_service import (
    process_pdf,
    get_document_info,
    get_documents_info,
    delete_document_info,
    get_document_chunks
)
# Keep reference to original DocumentService for future use if needed
from app.services.document import DocumentService as OriginalDocumentService
from app.db.session import get_db


router = APIRouter(tags=["Documents"])

# Initialize logger
logger = logging.getLogger(__name__)


# Dependency injection
def get_document_service():
    """
    Get document service instance.
    
    Returns:
        DocumentService instance
    """
    # This is kept for compatibility but not currently used
    return OriginalDocumentService()


# @router.post("/", response_model=DocumentResponse)
# async def upload_document(
#     file: UploadFile = File(...),
#     title: str = Form(...),
#     category: Optional[str] = Form(None),
#     tags: Optional[str] = Form(None),
#     db: AsyncSession = Depends(get_db)
# ):
#     """
#     Upload and process a document.
#     This is to match the PLANNING.md API design.
#     Currently, only PDF documents are supported.
#     
#     Args:
#         file: The document file to upload
#         title: Document title
#         category: Optional document category
#         tags: Optional comma-separated tags
#         db: AsyncSession instance
#         
#     Returns:
#         DocumentResponse with document ID and status
#     """
#     # Forward to the upload_pdf endpoint
#     return await upload_pdf(file, title, category, tags, db)


# @router.post("/upload-pdf", response_model=DocumentResponse)
# async def upload_pdf(
#     file: UploadFile = File(...),
#     title: str = Form(...),
#     category: Optional[str] = Form(None),
#     tags: Optional[str] = Form(None),
#     db: AsyncSession = Depends(get_db)
# ):
#     """
#     Upload and process a PDF document.
#     
#     Args:
#         file: The PDF file to upload
#         title: Optional document title (defaults to filename)
#         category: Optional document category
#         tags: Optional comma-separated tags
#         db: AsyncSession instance
#         
#     Returns:
#         DocumentResponse with document ID and status
#     """
#     if not file.filename.lower().endswith('.pdf'):
#         raise HTTPException(status_code=400, detail="File must be a PDF")
#     
#     try:
#         document = await process_pdf(file, title, category, tags, db)
#         return DocumentResponse(
#             document_id=document.document_id,
#             message=f"Document '{document.title}' processed successfully"
#         )
#         
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
#     finally:
#         await file.close()


# @router.get("", response_model=List[DocumentInfo])
# async def list_documents(
#     category: Optional[str] = None,
#     tag: Optional[str] = None,
#     db: AsyncSession = Depends(get_db)
# ):
#     """
#     List all processed documents.
#     
#     Args:
#         category: Optional category filter
#         tag: Optional tag filter
#         db: AsyncSession instance
#         
#     Returns:
#         List of DocumentInfo objects
#     """
#     # Pass parameters in the correct order: session, category, tags
#     tags_list = [tag] if tag else None
#     return await get_documents_info(db, category, tags_list)


# @router.get("/{document_id}", response_model=DocumentInfo)
# async def get_document(
#     document_id: str,
#     db: AsyncSession = Depends(get_db)
# ):
#     """
#     Get document details.
#     
#     Args:
#         document_id: The document ID to retrieve
#         db: AsyncSession instance
#         
#     Returns:
#         DocumentInfo with document details
#     """
#     try:
#         return await get_document_info(document_id, db)
#     except ValueError:
#         raise HTTPException(status_code=404, detail="Document not found")


# @router.delete("/{document_id}", response_model=DocumentResponse)
# async def delete_document(
#     document_id: str,
#     db: AsyncSession = Depends(get_db)
# ):
#     """
#     Delete a document.
#     
#     Args:
#         document_id: The document ID to delete
#         db: AsyncSession instance
#         
#     Returns:
#         DocumentResponse with status
#     """
#     await delete_document_info(document_id, db)
#     return DocumentResponse(
#         document_id=document_id,
#         message=f"Document {document_id} deleted successfully"
#     )


# @router.get("/{document_id}/chunks")
# async def get_chunks(
#     document_id: str,
#     db: AsyncSession = Depends(get_db)
# ):
#     """
#     Get document chunks by ID.
#     
#     Args:
#         document_id: The document ID to retrieve chunks for
#         db: AsyncSession instance
#         
#     Returns:
#         List of document chunks
#     """
#     return await get_document_chunks(document_id, db) 