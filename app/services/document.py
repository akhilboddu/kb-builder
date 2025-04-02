"""
Service for processing PDF documents.
"""
import logging
import uuid
import tempfile
import os
from typing import List, Dict, Any, Tuple, Optional
from fastapi import BackgroundTasks
import fitz  # PyMuPDF

from app.db.vector_store import add_chunks_to_vector_store
from app.db.document_repository import save_document, get_document, get_documents, delete_document
from app.utils.text_processing import split_text_into_chunks
from app.models.document import DocumentInfo, DocumentChunk


logger = logging.getLogger(__name__)


class DocumentService:
    """Service for managing document operations."""
    
    def __init__(self):
        """Initialize the document service."""
        pass
    
    async def process_pdf(
        self,
        content: bytes,
        filename: str,
        title: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> str:
        """
        Process a PDF document and add to knowledge base.
        
        Args:
            content: Raw PDF file content
            filename: Original filename
            title: Document title
            category: Optional category
            tags: Optional tags
            background_tasks: FastAPI background tasks
            
        Returns:
            document_id: Generated document ID
        """
        # Generate document ID
        document_id = f"doc-{str(uuid.uuid4())}"
        
        # Create initial document info
        document_info = DocumentInfo(
            document_id=document_id,
            title=title,
            filename=filename,
            category=category,
            tags=tags or [],
            page_count=0,
            chunk_count=0,
            processing_status="processing"
        )
        
        # Save initial document info
        await save_document(document_info)
        
        # Process in background if background_tasks is provided
        if background_tasks:
            background_tasks.add_task(
                self._process_pdf_content,
                content=content,
                document_info=document_info
            )
        else:
            await self._process_pdf_content(content, document_info)
        
        return document_id
    
    async def _process_pdf_content(self, content: bytes, document_info: DocumentInfo) -> None:
        """
        Process PDF content and extract text.
        
        Args:
            content: Raw PDF file content
            document_info: Document information
        """
        try:
            # Create a temporary file to write the PDF content
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name
            
            try:
                # Open the PDF file
                pdf_document = fitz.open(temp_path)
                
                # Update document info with page count
                document_info.page_count = len(pdf_document)
                logger.info(f"Processing document {document_info.document_id} with {document_info.page_count} pages")
                
                # Process each page
                all_chunks = []
                
                for page_num, page in enumerate(pdf_document):
                    # Extract text from page
                    text = page.get_text("text")
                    
                    if not text.strip():
                        logger.warning(f"No text found on page {page_num+1}")
                        continue
                    
                    # Split text into chunks
                    chunks = split_text_into_chunks(
                        content=text,
                        title=f"{document_info.title} - Page {page_num+1}"
                    )
                    
                    # Create chunks with metadata
                    for i, chunk_text in enumerate(chunks):
                        chunk = DocumentChunk(
                            document_id=document_info.document_id,
                            content=chunk_text,
                            page_number=page_num + 1,
                            metadata={
                                "title": document_info.title,
                                "filename": document_info.filename,
                                "page": page_num + 1,
                                "category": document_info.category,
                                "tags": document_info.tags,
                                "chunk_index": i,
                                "type": "pdf"
                            }
                        )
                        all_chunks.append(chunk)
                
                # Prepare chunks for vector store
                chunks_with_metadata = [
                    {
                        "content": chunk.content,
                        "metadata": {
                            "document_id": chunk.document_id,
                            "page_number": chunk.page_number,
                            "title": document_info.title,
                            "category": document_info.category,
                            "tags": document_info.tags,
                            "type": "pdf"
                        }
                    }
                    for chunk in all_chunks
                ]
                
                # Add to vector store
                await add_chunks_to_vector_store(chunks_with_metadata)
                
                # Update document info
                document_info.chunk_count = len(all_chunks)
                document_info.processing_status = "completed"
                await save_document(document_info)
                
                logger.info(f"Document {document_info.document_id} processed with {len(all_chunks)} chunks")
                
            finally:
                # Close the document
                if 'pdf_document' in locals():
                    pdf_document.close()
                
                # Delete the temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.error(f"Error processing document {document_info.document_id}: {str(e)}")
            document_info.processing_status = "failed"
            await save_document(document_info)
            raise
    
    async def get_document(self, document_id: str) -> Optional[DocumentInfo]:
        """
        Get document details by ID.
        
        Args:
            document_id: Document ID to retrieve
            
        Returns:
            DocumentInfo if found, None otherwise
        """
        return await get_document(document_id)
    
    async def get_documents(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None
    ) -> List[DocumentInfo]:
        """
        Get all documents, optionally filtered.
        
        Args:
            category: Optional category filter
            tag: Optional tag filter
            
        Returns:
            List of DocumentInfo objects
        """
        return await get_documents(category, tag)
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document by ID.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            True if document was deleted, False otherwise
        """
        return await delete_document(document_id)


# Service instance
_document_service = None


def get_document_service() -> DocumentService:
    """Get the document service instance."""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service


# For backward compatibility
async def process_pdf_document(
    content: bytes,
    filename: str,
    title: str,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    background_tasks: Optional[BackgroundTasks] = None
) -> str:
    """Legacy function for processing PDF documents."""
    service = get_document_service()
    return await service.process_pdf(content, filename, title, category, tags, background_tasks)


async def get_document_by_id(document_id: str) -> Optional[DocumentInfo]:
    """Legacy function for getting document by ID."""
    service = get_document_service()
    return await service.get_document(document_id)


async def get_all_documents(
    category: Optional[str] = None,
    tag: Optional[str] = None
) -> List[DocumentInfo]:
    """Legacy function for getting all documents."""
    service = get_document_service()
    return await service.get_documents(category, tag)