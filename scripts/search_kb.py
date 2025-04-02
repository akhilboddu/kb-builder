#!/usr/bin/env python
"""
Script to directly search the knowledge base using the vector store.
This bypasses the API and accesses the vector store directly.
"""

import os
import sys
import argparse
import asyncio
from typing import List, Dict, Any
import logging

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def search_knowledge_base(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search the knowledge base using the vector store directly.
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        
    Returns:
        List of search results with text and metadata
    """
    try:
        # Import here to avoid loading until needed
        from app.db.vector_store import search_vector_store
        
        logger.info(f"Searching for: '{query}'")
        
        # Use the search_vector_store function
        results = await search_vector_store(query=query, n_results=limit)
        
        # Format the results
        formatted_results = []
        
        # ChromaDB returns results in a dictionary with lists
        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        distances = results.get("distances", [])
        
        for i in range(len(documents[0]) if documents else 0):
            # Each list is actually a list of lists where the outer list is for different queries
            # Since we only have one query, we access index 0
            doc = documents[0][i] if documents else ""
            metadata = metadatas[0][i] if metadatas else {}
            distance = distances[0][i] if distances else 1.0
            
            similarity = 1.0 - distance  # Convert distance to similarity
            formatted_results.append({
                "text": doc,
                "metadata": metadata,
                "similarity": similarity
            })
            
        logger.info(f"Found {len(formatted_results)} results")
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def display_results(results: List[Dict[str, Any]]) -> None:
    """Display search results in a formatted way."""
    if not results:
        print("No results found.")
        return
        
    print(f"\nFound {len(results)} results:\n")
    
    for i, result in enumerate(results):
        print(f"Result {i+1}:")
        print(f"Text: {result['text'][:150]}...")
        print(f"Source: {result['metadata'].get('source', 'Unknown')}")
        print(f"URL: {result['metadata'].get('url', 'N/A')}")
        print(f"Similarity: {result['similarity']:.4f}")
        print("-" * 50)

async def async_main():
    """Async main function to handle async operations."""
    parser = argparse.ArgumentParser(description="Search the knowledge base directly")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of results to return")
    
    args = parser.parse_args()
    
    results = await search_knowledge_base(args.query, args.limit)
    display_results(results)

def main():
    """Entry point that runs the async function."""
    asyncio.run(async_main())

if __name__ == "__main__":
    main() 