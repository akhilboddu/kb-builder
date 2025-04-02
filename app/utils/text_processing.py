"""
Text processing utilities for chunking and cleaning text.
"""
import re
from typing import List, Optional


def clean_text(text: str) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    # Remove unwanted characters
    text = re.sub(r'[^\w\s.,;:!?\'"-]', ' ', text)
    
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Fix spacing around punctuation
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    
    # Trim whitespace
    text = text.strip()
    
    return text


def split_text_into_chunks(
    content: str,
    title: Optional[str] = None,
    max_chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[str]:
    """
    Split text into chunks for embedding.
    
    Args:
        content: Text content to split
        title: Optional title to prepend to chunks
        max_chunk_size: Maximum chunk size in characters
        chunk_overlap: Overlap between chunks in characters
        
    Returns:
        List of text chunks
    """
    # Clean the content
    content = clean_text(content)
    
    # If content is small enough, return as a single chunk
    if len(content) <= max_chunk_size:
        chunk = title + ": " + content if title else content
        return [chunk]
    
    # Force split into sentences if paragraphs are too large
    sentences = re.split(r'(?<=[.!?])\s+', content)
    
    chunks = []
    current_chunk = ""
    
    # Process sentences into chunks
    for sentence in sentences:
        # If this sentence alone is larger than max_chunk_size, we need to split it
        if len(sentence) > max_chunk_size:
            # If we have accumulated content, add it as a chunk
            if current_chunk:
                if title:
                    chunks.append(title + ": " + current_chunk)
                else:
                    chunks.append(current_chunk)
                current_chunk = ""
            
            # Split the long sentence into smaller parts
            for i in range(0, len(sentence), max_chunk_size - chunk_overlap):
                chunk_part = sentence[i:i + max_chunk_size]
                if i > 0:  # Not the first part
                    # Add overlap from previous part
                    start_idx = max(0, i - chunk_overlap)
                    chunk_part = sentence[start_idx:i + max_chunk_size]
                
                if title:
                    chunks.append(title + ": " + chunk_part)
                else:
                    chunks.append(chunk_part)
                
        # If adding this sentence would exceed max_chunk_size, start a new chunk
        elif len(current_chunk) + len(sentence) + 1 > max_chunk_size:
            if current_chunk:
                # Add title to chunk if provided
                if title:
                    chunks.append(title + ": " + current_chunk)
                else:
                    chunks.append(current_chunk)
                
                # Start new chunk with overlap if possible
                if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                    # Try to find a sentence boundary for the overlap
                    overlap_sentences = re.findall(r'[^.!?]+[.!?]', current_chunk[-chunk_overlap:])
                    if overlap_sentences:
                        current_chunk = overlap_sentences[-1] + " "
                    else:
                        # Fall back to character-based overlap
                        current_chunk = current_chunk[-chunk_overlap:] + " "
                else:
                    current_chunk = ""
            
            current_chunk += sentence + " "
        else:
            # Add sentence to current chunk
            current_chunk += sentence + " "
    
    # Add the last chunk if it's not empty
    if current_chunk.strip():
        if title:
            chunks.append(title + ": " + current_chunk)
        else:
            chunks.append(current_chunk)
    
    return chunks


def extract_semantic_chunks(content: str, headings: List[dict]) -> List[str]:
    """
    Extract semantic chunks based on headings and their content.
    
    Args:
        content: Full text content
        headings: List of heading dictionaries with 'level' and 'text' keys
        
    Returns:
        List of semantic chunks
    """
    # Not implemented yet - this would extract content by headings 
    # For now, just use regular chunking
    return split_text_into_chunks(content)