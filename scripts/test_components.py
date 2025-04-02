#!/usr/bin/env python
"""
Test script for KB Builder components.
This script allows testing various components independently.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

def test_text_processing():
    """Test text processing utilities"""
    from app.utils.text_processing import clean_text, split_text_into_chunks
    
    # Test clean_text
    original_text = "This is a   sample text with \n\n newlines and $%^& special characters."
    cleaned_text = clean_text(original_text)
    print(f"Original: {original_text}")
    print(f"Cleaned: {cleaned_text}")
    
    # Test text chunking
    large_text = "This is " + "a very long text. " * 100
    chunks = split_text_into_chunks(large_text, max_chunk_size=100, chunk_overlap=20)
    print(f"\nSplit text into {len(chunks)} chunks")
    print(f"First chunk: {chunks[0][:50]}...")
    print(f"Last chunk: {chunks[-1][:50]}...")

def test_web_crawler():
    """Test web crawler integration"""
    try:
        from app.services.web_crawler_service import WebCrawlerService
        
        service = WebCrawlerService()
        url = "https://example.com"
        print(f"Crawling {url}...")
        result = service.crawl_website(url=url, max_pages=1, max_depth=1)
        print(f"Crawled {len(result.pages)} pages")
        for page in result.pages:
            print(f"Title: {page.title}")
            print(f"URL: {page.url}")
            print(f"Content preview: {page.content[:100]}...")
            print("---")
            
    except ImportError as e:
        print(f"Error: {e}")
        print("Web crawler service may not be fully implemented yet.")

def test_document_processing():
    """Test document processing"""
    try:
        from app.services.document_service import DocumentService
        
        service = DocumentService()
        print("Document processing service initialized")
        # Add sample document processing tests here
            
    except ImportError as e:
        print(f"Error: {e}")
        print("Document service may not be fully implemented yet.")

def test_vector_store():
    """Test vector store operations"""
    try:
        from app.db.vector_store import VectorStore
        
        store = VectorStore()
        print("Vector store initialized")
        
        # Test adding a document
        test_doc = {
            "id": "test1",
            "text": "This is a test document for vector storage",
            "metadata": {"source": "test", "category": "general"}
        }
        
        print(f"Adding document: {test_doc['id']}")
        store.add_texts([test_doc['text']], [test_doc['metadata']])
        
        # Test querying
        query = "test document"
        print(f"Querying: '{query}'")
        results = store.similarity_search(query, k=1)
        for idx, result in enumerate(results):
            print(f"Result {idx+1}:")
            print(f"Text: {result.page_content[:100]}...")
            print(f"Metadata: {result.metadata}")
            
    except ImportError as e:
        print(f"Error: {e}")
        print("Vector store may not be fully implemented yet.")

def main():
    parser = argparse.ArgumentParser(description="Test KB Builder components")
    parser.add_argument("component", choices=["text", "crawler", "document", "vector", "all"],
                        help="Component to test")
    
    args = parser.parse_args()
    
    if args.component == "text" or args.component == "all":
        print("\n===== Testing Text Processing =====")
        test_text_processing()
        
    if args.component == "crawler" or args.component == "all":
        print("\n===== Testing Web Crawler =====")
        test_web_crawler()
        
    if args.component == "document" or args.component == "all":
        print("\n===== Testing Document Processing =====")
        test_document_processing()
        
    if args.component == "vector" or args.component == "all":
        print("\n===== Testing Vector Store =====")
        test_vector_store()

if __name__ == "__main__":
    main() 