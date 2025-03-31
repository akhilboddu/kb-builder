import logging
import PyPDF2
import tiktoken
import uuid
from app.models.knowledge_base import DocumentChunk, DocumentMetadata, WebpageData
from app.services.embedding_service import generate_embeddings_batch
from app.core.config import settings
from app.core.database import supabase_client
from typing import List, Dict, Any, Tuple
from datetime import datetime
from fastapi import UploadFile
import io

logger = logging.getLogger(__name__)

# Get the encoding for token counting
encoding = tiktoken.encoding_for_model("gpt-4")

async def chunk_text(text: str, metadata: Dict[str, Any], max_tokens: int = None) -> List[DocumentChunk]:
    """
    Split text into chunks based on token count.
    
    Args:
        text: Text to split into chunks
        metadata: Metadata to include with each chunk
        max_tokens: Maximum number of tokens per chunk
        
    Returns:
        List of DocumentChunk objects
    """
    if max_tokens is None:
        max_tokens = settings.MAX_CHUNK_SIZE
    
    # Count tokens in the text
    tokens = encoding.encode(text)
    
    chunks = []
    current_chunk_tokens = []
    
    for token in tokens:
        current_chunk_tokens.append(token)
        
        # If current chunk exceeds max_tokens, create a new chunk
        if len(current_chunk_tokens) >= max_tokens:
            chunk_text = encoding.decode(current_chunk_tokens)
            chunks.append(DocumentChunk(
                text=chunk_text,
                metadata=metadata
            ))
            current_chunk_tokens = []
    
    # Add the last chunk if it's not empty
    if current_chunk_tokens:
        chunk_text = encoding.decode(current_chunk_tokens)
        chunks.append(DocumentChunk(
            text=chunk_text,
            metadata=metadata
        ))
    
    return chunks

async def process_pdf_file(file: UploadFile, document_id: str, metadata: DocumentMetadata) -> Tuple[int, List[str]]:
    """
    Process a PDF file, extract text, and create chunks.
    
    Args:
        file: The uploaded PDF file
        document_id: The document ID in the database
        metadata: Document metadata
        
    Returns:
        Tuple of (number of chunks processed, list of chunk IDs)
    """
    try:
        # Read the file
        contents = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))
        
        text = ""
        # Extract text from each page
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n\n"
        
        # Create chunks
        chunks = await chunk_text(text, metadata.model_dump())
        
        # Generate embeddings for all chunks in a batch
        texts = [chunk.text for chunk in chunks]
        embeddings = await generate_embeddings_batch(texts)
        
        # Store chunks in the database
        chunk_ids = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = str(uuid.uuid4())
            chunk_ids.append(chunk_id)
            
            # Store in database
            supabase_client.table("document_chunks").insert({
                "id": chunk_id,
                "document_id": document_id,
                "content": chunk.text,
                "metadata": chunk.metadata,
                "embedding": embedding,
                "embedding_model": settings.EMBEDDING_MODEL,
                "created_at": datetime.now().isoformat()
            }).execute()
        
        return len(chunks), chunk_ids
    except Exception as e:
        logger.error(f"Error processing PDF file: {str(e)}")
        raise

async def process_webpage_data(webpage_data: WebpageData, document_id: str, metadata: DocumentMetadata) -> Tuple[int, List[str]]:
    """
    Process webpage data from the web scraper.
    
    Args:
        webpage_data: The scraped webpage data
        document_id: The document ID in the database
        metadata: Document metadata
        
    Returns:
        Tuple of (number of chunks processed, list of chunk IDs)
    """
    try:
        # Extract content from the webpage data
        title = f"# {webpage_data.title}\n\n"
        
        content = title
        
        # Process headings and paragraphs
        content_items = []
        
        # Sort headings and paragraphs by their IDs to maintain order
        for heading in webpage_data.headings:
            content_items.append({"type": "heading", "text": f"{'#' * heading.level} {heading.text}", "id": heading.id})
        
        for paragraph in webpage_data.paragraphs:
            content_items.append({"type": "paragraph", "text": paragraph.text, "id": paragraph.id})
            
        # Sort by ID to maintain the original order
        content_items.sort(key=lambda x: x["id"])
        
        # Combine the sorted content
        for item in content_items:
            content += item["text"] + "\n\n"
            
        # Add links at the end
        if webpage_data.links:
            content += "## Links\n\n"
            for link in webpage_data.links:
                content += f"- [{link.text}]({link.url})\n"
        
        # Create chunks
        chunks = await chunk_text(content, metadata.model_dump())
        
        # Generate embeddings for all chunks in a batch
        texts = [chunk.text for chunk in chunks]
        embeddings = await generate_embeddings_batch(texts)
        
        # Store chunks in the database
        chunk_ids = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = str(uuid.uuid4())
            chunk_ids.append(chunk_id)
            
            # Store in database
            supabase_client.table("document_chunks").insert({
                "id": chunk_id,
                "document_id": document_id,
                "content": chunk.text,
                "metadata": chunk.metadata,
                "embedding": embedding,
                "embedding_model": settings.EMBEDDING_MODEL,
                "created_at": datetime.now().isoformat()
            }).execute()
        
        return len(chunks), chunk_ids
    except Exception as e:
        logger.error(f"Error processing webpage data: {str(e)}")
        raise