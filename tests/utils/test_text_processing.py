"""
Tests for text processing utilities.
"""
import pytest
from app.utils.text_processing import clean_text, split_text_into_chunks


def test_clean_text():
    """Test text cleaning functionality."""
    # Test with multiple whitespace
    assert clean_text("This   has   extra   spaces") == "This has extra spaces"
    
    # Test with unwanted characters
    assert clean_text("Text with @#$ symbols") == "Text with symbols"
    
    # Test with punctuation spacing
    assert clean_text("Hello , world !") == "Hello, world!"
    
    # Test with multiple issues
    assert clean_text("  This  text  needs @#$  cleaning  ,  badly  ") == "This text needs cleaning, badly"


def test_split_text_into_chunks_small_content():
    """Test text chunking with content smaller than max chunk size."""
    content = "This is a small piece of content that should fit in one chunk."
    chunks = split_text_into_chunks(content, max_chunk_size=1000)
    
    assert len(chunks) == 1
    assert chunks[0] == content


def test_split_text_into_chunks_with_title():
    """Test text chunking with title."""
    content = "This is content that should have a title."
    title = "Sample Title"
    chunks = split_text_into_chunks(content, title=title, max_chunk_size=1000)
    
    assert len(chunks) == 1
    assert chunks[0] == f"{title}: {content}"


def test_split_text_into_chunks_large_content():
    """Test text chunking with content larger than max chunk size."""
    # Create a large content with paragraphs
    paragraph = "This is a test paragraph that will be repeated to create content larger than the max chunk size. " * 10
    paragraphs = [paragraph] * 5
    content = "\n\n".join(paragraphs)
    
    # Use a very small max_chunk_size to force splitting
    chunks = split_text_into_chunks(content, max_chunk_size=100, chunk_overlap=20)
    
    # Should be split into multiple chunks
    assert len(chunks) > 1
    
    # Check that first and second chunks are different
    assert chunks[0] != chunks[1] 