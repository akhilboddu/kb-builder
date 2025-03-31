import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Body
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from app.models.knowledge_base import (
    KnowledgeBase, KnowledgeBaseCreate, Document, DocumentCreate, 
    DocumentStatus, DocumentMetadata, WebpageData
)
from app.models.user import User
from app.core.dependencies import get_current_user, validate_bot_access
from app.core.database import supabase_client
from app.core.config import settings
from app.services.document_processor import process_pdf_file, process_webpage_data
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/create", response_model=KnowledgeBase)
async def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    user: User = Depends(get_current_user)
):
    """
    Create a new knowledge base for a bot.
    """
    try:
        # Verify bot access
        await validate_bot_access(kb_data.bot_id, user)
        
        # Check if user has reached their knowledge base limit
        kb_count_response = supabase_client.table("knowledge_bases").select(
            "count", count="exact"
        ).eq("bot_id", kb_data.bot_id).execute()
        
        kb_count = kb_count_response.count
        
        if kb_count >= user.limits.max_kb_per_bot:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Maximum number of knowledge bases reached ({user.limits.max_kb_per_bot})"
            )
        
        # Create knowledge base
        kb_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        kb_data_dict = {
            "id": kb_id,
            "bot_id": kb_data.bot_id,
            "name": kb_data.name,
            "created_at": timestamp
        }
        
        response = supabase_client.table("knowledge_bases").insert(kb_data_dict).execute()
        
        # Return the created knowledge base
        return KnowledgeBase(
            id=kb_id,
            bot_id=kb_data.bot_id,
            name=kb_data.name,
            created_at=datetime.fromisoformat(timestamp)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating knowledge base: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create knowledge base"
        )

@router.get("/list/{bot_id}", response_model=List[KnowledgeBase])
async def list_knowledge_bases(
    bot_id: str,
    user: User = Depends(get_current_user)
):
    """
    List all knowledge bases for a bot.
    """
    try:
        # Verify bot access
        await validate_bot_access(bot_id, user)
        
        # Get knowledge bases
        response = supabase_client.table("knowledge_bases").select("*").eq("bot_id", bot_id).execute()
        
        # Convert to model
        knowledge_bases = []
        for kb_data in response.data:
            knowledge_bases.append(KnowledgeBase(
                id=kb_data["id"],
                bot_id=kb_data["bot_id"],
                name=kb_data["name"],
                created_at=datetime.fromisoformat(kb_data["created_at"])
            ))
            
        return knowledge_bases
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing knowledge bases: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list knowledge bases"
        )

@router.post("/documents/upload", response_model=Document)
async def upload_document(
    file: UploadFile = File(...),
    knowledge_base_id: str = Form(...),
    title: str = Form(...),
    user: User = Depends(get_current_user)
):
    """
    Upload a document (PDF) to a knowledge base.
    """
    try:
        # Get the knowledge base to verify access
        kb_response = supabase_client.table("knowledge_bases").select("*").eq("id", knowledge_base_id).execute()
        
        if not kb_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found"
            )
            
        bot_id = kb_response.data[0]["bot_id"]
        
        # Verify bot access
        await validate_bot_access(bot_id, user)
        
        # Verify file size
        content_length = file.size
        if content_length > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB limit"
            )
            
        # Verify file extension
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
            
        # Check document count limit
        doc_count_response = supabase_client.table("documents").select(
            "count", count="exact"
        ).eq("knowledge_base_id", knowledge_base_id).execute()
        
        doc_count = doc_count_response.count
        
        if doc_count >= user.limits.max_documents_per_kb:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Maximum number of documents reached ({user.limits.max_documents_per_kb})"
            )
            
        # Create document entry
        document_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Create metadata
        metadata = DocumentMetadata(
            title=title,
            filetype="pdf",
            created_at=datetime.now(),
            chunk_count=0
        )
        
        # Create document in database
        document_data = {
            "id": document_id,
            "knowledge_base_id": knowledge_base_id,
            "title": title,
            "status": DocumentStatus.PROCESSING.value,
            "metadata": metadata.model_dump(),
            "created_at": timestamp
        }
        
        response = supabase_client.table("documents").insert(document_data).execute()
        
        # Process the document in the background
        try:
            # Process the PDF file
            chunk_count, chunk_ids = await process_pdf_file(file, document_id, metadata)
            
            # Update document with processing results
            metadata.chunk_count = chunk_count
            
            supabase_client.table("documents").update({
                "status": DocumentStatus.COMPLETED.value,
                "metadata": metadata.model_dump()
            }).eq("id", document_id).execute()
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            
            # Update document with error status
            supabase_client.table("documents").update({
                "status": DocumentStatus.FAILED.value
            }).eq("id", document_id).execute()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process document"
            )
            
        # Return the created document
        return Document(
            id=document_id,
            knowledge_base_id=knowledge_base_id,
            title=title,
            status=DocumentStatus.COMPLETED,
            metadata=metadata,
            created_at=datetime.fromisoformat(timestamp)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document"
        )

@router.post("/documents/webpage", response_model=Document)
async def process_webpage(
    webpage_data: WebpageData,
    knowledge_base_id: str,
    user: User = Depends(get_current_user)
):
    """
    Process webpage data from the web scraper.
    """
    try:
        # Get the knowledge base to verify access
        kb_response = supabase_client.table("knowledge_bases").select("*").eq("id", knowledge_base_id).execute()
        
        if not kb_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found"
            )
            
        bot_id = kb_response.data[0]["bot_id"]
        
        # Verify bot access
        await validate_bot_access(bot_id, user)
        
        # Check document count limit
        doc_count_response = supabase_client.table("documents").select(
            "count", count="exact"
        ).eq("knowledge_base_id", knowledge_base_id).execute()
        
        doc_count = doc_count_response.count
        
        if doc_count >= user.limits.max_documents_per_kb:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Maximum number of documents reached ({user.limits.max_documents_per_kb})"
            )
            
        # Create document entry
        document_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Create metadata
        metadata = DocumentMetadata(
            source_url=webpage_data.url,
            title=webpage_data.title,
            filetype="webpage",
            created_at=datetime.now(),
            chunk_count=0
        )
        
        # Create document in database
        document_data = {
            "id": document_id,
            "knowledge_base_id": knowledge_base_id,
            "title": webpage_data.title,
            "status": DocumentStatus.PROCESSING.value,
            "metadata": metadata.model_dump(),
            "created_at": timestamp
        }
        
        response = supabase_client.table("documents").insert(document_data).execute()
        
        # Process the webpage data
        try:
            # Process the webpage data
            chunk_count, chunk_ids = await process_webpage_data(webpage_data, document_id, metadata)
            
            # Update document with processing results
            metadata.chunk_count = chunk_count
            
            supabase_client.table("documents").update({
                "status": DocumentStatus.COMPLETED.value,
                "metadata": metadata.model_dump()
            }).eq("id", document_id).execute()
            
        except Exception as e:
            logger.error(f"Error processing webpage: {str(e)}")
            
            # Update document with error status
            supabase_client.table("documents").update({
                "status": DocumentStatus.FAILED.value
            }).eq("id", document_id).execute()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process webpage data"
            )
            
        # Return the created document
        return Document(
            id=document_id,
            knowledge_base_id=knowledge_base_id,
            title=webpage_data.title,
            status=DocumentStatus.COMPLETED,
            metadata=metadata,
            created_at=datetime.fromisoformat(timestamp)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webpage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webpage data"
        )

@router.get("/documents/{knowledge_base_id}", response_model=List[Document])
async def list_documents(
    knowledge_base_id: str,
    user: User = Depends(get_current_user)
):
    """
    List all documents in a knowledge base.
    """
    try:
        # Get the knowledge base to verify access
        kb_response = supabase_client.table("knowledge_bases").select("*").eq("id", knowledge_base_id).execute()
        
        if not kb_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found"
            )
            
        bot_id = kb_response.data[0]["bot_id"]
        
        # Verify bot access
        await validate_bot_access(bot_id, user)
        
        # Get documents
        response = supabase_client.table("documents").select("*").eq("knowledge_base_id", knowledge_base_id).execute()
        
        # Convert to model
        documents = []
        for doc_data in response.data:
            # Create metadata object
            metadata = DocumentMetadata.model_validate(doc_data["metadata"])
            
            documents.append(Document(
                id=doc_data["id"],
                knowledge_base_id=doc_data["knowledge_base_id"],
                title=doc_data["title"],
                status=DocumentStatus(doc_data["status"]),
                metadata=metadata,
                created_at=datetime.fromisoformat(doc_data["created_at"])
            ))
            
        return documents
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents"
        )