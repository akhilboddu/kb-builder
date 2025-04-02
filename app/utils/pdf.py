"""PDF processing utilities."""
import logging
import fitz  # PyMuPDF
from typing import List

# Initialize logger
logger = logging.getLogger(__name__)

def extract_text_from_pdf(content: bytes) -> tuple[List[str], int]:
    """
    Extract text from PDF content.
    
    Args:
        content: Raw PDF file content
        
    Returns:
        Tuple of (list of text content for each page, total page count)
    """
    # Create PDF document from bytes
    pdf_document = fitz.open(stream=content, filetype="pdf")
    
    try:
        # Extract text from each page
        pages = []
        total_pages = len(pdf_document)
        
        for page in pdf_document:
            text = page.get_text("text")
            if text.strip():
                pages.append(text)
            else:
                logger.warning(f"No text found on page {page.number + 1}")
        
        return pages, total_pages
        
    finally:
        pdf_document.close()

def split_text_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Text to split
        chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    # Split text into sentences
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        # Add sentence length plus space
        sentence_size = len(sentence) + 1
        
        if current_size + sentence_size > chunk_size and current_chunk:
            # Join current chunk and add to chunks
            chunks.append(" ".join(current_chunk))
            
            # Keep last sentences for overlap
            overlap_size = 0
            overlap_chunk = []
            
            for s in reversed(current_chunk):
                if overlap_size + len(s) + 1 <= overlap:
                    overlap_chunk.insert(0, s)
                    overlap_size += len(s) + 1
                else:
                    break
            
            # Start new chunk with overlap
            current_chunk = overlap_chunk
            current_size = overlap_size
        
        current_chunk.append(sentence)
        current_size += sentence_size
    
    # Add final chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks 