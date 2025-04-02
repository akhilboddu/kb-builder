#!/usr/bin/env python
"""
Knowledge Base Builder Example

This script demonstrates how to use the KB Builder to:
1. Crawl a website
2. Process a PDF document
3. Search the knowledge base
"""

import os
import requests
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the path (for local development)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

# Default API URL (adjust as needed)
API_URL = "http://localhost:8000"

def crawl_website(url, max_pages=5, max_depth=2):
    """
    Crawl a website and add it to the knowledge base
    """
    print(f"Crawling website: {url} (max_pages={max_pages}, max_depth={max_depth})")
    
    endpoint = f"{API_URL}/api/crawl"
    payload = {
        "url": url,
        "max_pages": max_pages,
        "max_depth": max_depth
    }
    
    response = requests.post(endpoint, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Crawl job initiated: {result.get('job_id')}")
        return result
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def process_pdf(pdf_path):
    """
    Process a PDF document and add it to the knowledge base
    """
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        return None
    
    print(f"Processing PDF: {pdf_path}")
    
    endpoint = f"{API_URL}/api/documents"
    
    with open(pdf_path, "rb") as pdf_file:
        files = {"file": (os.path.basename(pdf_path), pdf_file, "application/pdf")}
        response = requests.post(endpoint, files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Document processed: {result.get('document_id')}")
        return result
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def search_knowledge_base(query, limit=5):
    """
    Search the knowledge base
    """
    print(f"Searching knowledge base for: '{query}'")
    
    endpoint = f"{API_URL}/api/search"
    params = {"query": query, "limit": limit}
    
    response = requests.get(endpoint, params=params)
    
    if response.status_code == 200:
        results = response.json()
        print(f"Found {len(results)} results:")
        
        for i, result in enumerate(results):
            print(f"\nResult {i+1}:")
            print(f"Text: {result.get('text')[:150]}...")
            print(f"Source: {result.get('metadata', {}).get('source')}")
            print(f"Similarity: {result.get('similarity', 0):.4f}")
        
        return results
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def main():
    """Main function to demonstrate KB Builder usage"""
    # Create examples directory if it doesn't exist
    Path("examples/data").mkdir(parents=True, exist_ok=True)
    
    print("\n=== Knowledge Base Builder Example ===\n")
    
    # Example 1: Crawl a website
    print("\n--- Example 1: Web Crawler ---")
    crawl_result = crawl_website(
        url="https://en.wikipedia.org/wiki/Knowledge_base",
        max_pages=3,
        max_depth=1
    )
    
    # Example 2: Process a PDF (comment out if no PDF available)
    print("\n--- Example 2: PDF Processing ---")
    print("Skipping PDF processing in this example (no sample PDF provided)")
    # Uncomment to process a PDF:
    # pdf_result = process_pdf("examples/data/sample.pdf")
    
    # Example 3: Search the knowledge base
    print("\n--- Example 3: Knowledge Base Search ---")
    print("Waiting a moment for crawled content to be processed...")
    import time
    time.sleep(5)  # Wait for processing to complete
    
    search_result = search_knowledge_base("What is a knowledge base?")
    
    print("\n=== Example Complete ===")

if __name__ == "__main__":
    main() 