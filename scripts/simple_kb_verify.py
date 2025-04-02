#!/usr/bin/env python
"""
Simple script to verify if liorra.io data exists in the knowledge base.
This script directly checks ChromaDB collections and counts documents.
"""

import os
import sys
import chromadb
from typing import Dict, Any, List
import logging

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_chroma_directory() -> str:
    """Get ChromaDB directory from settings or use default."""
    from dotenv import load_dotenv
    load_dotenv()
    
    return os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma")

def check_knowledge_base() -> None:
    """Check if the knowledge base exists and has documents."""
    try:
        # Get the ChromaDB directory
        chroma_dir = get_chroma_directory()
        logger.info(f"Checking ChromaDB at {chroma_dir}")
        
        # Make sure it exists
        if not os.path.exists(chroma_dir):
            logger.error(f"ChromaDB directory does not exist: {chroma_dir}")
            print(f"No knowledge base found at {chroma_dir}")
            return
        
        # Create a client
        client = chromadb.PersistentClient(path=chroma_dir)
        
        # List collections
        collection_names = client.list_collections()
        if not collection_names:
            logger.error("No collections found in ChromaDB")
            print("No collections found in the knowledge base")
            return
        
        print(f"\nFound {len(collection_names)} collection(s) in ChromaDB:")
        for coll_name in collection_names:
            # In v0.6.0+, list_collections returns collection names
            collection = client.get_collection(coll_name)
            count = collection.count()
            print(f"- {coll_name}: {count} documents")
            
            # Get some sample documents to check content
            if count > 0:
                sample = collection.peek(limit=3)
                print("\nSample documents:")
                for i, doc in enumerate(sample["documents"]):
                    metadata = sample["metadatas"][i] if "metadatas" in sample else {}
                    print(f"\nDocument {i+1}:")
                    print(f"Text: {doc[:150]}...")
                    print(f"Metadata: {metadata}")
                    
                # Check for liorra.io content
                print("\nChecking for liorra.io content:")
                liorra_found = False
                for i, metadata in enumerate(sample["metadatas"]):
                    url = metadata.get("url", "")
                    if "liorra.io" in url:
                        liorra_found = True
                        print(f"Found liorra.io content in document {i+1}")
                
                if not liorra_found:
                    print("No liorra.io content found in sample documents")
                    
                    # Try searching for liorra.io content
                    try:
                        # Search for documents containing 'liorra'
                        results = collection.query(
                            query_texts=["liorra"],
                            n_results=3
                        )
                        
                        if results["documents"][0]:
                            print(f"Found {len(results['documents'][0])} documents when searching for 'liorra'")
                            for i, doc in enumerate(results["documents"][0]):
                                metadata = results["metadatas"][0][i] if "metadatas" in results else {}
                                print(f"\nSearch Result {i+1}:")
                                print(f"Text: {doc[:150]}...")
                                print(f"Metadata: {metadata}")
                        else:
                            print("No documents found when searching for 'liorra'")
                    except Exception as e:
                        print(f"Could not perform search: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error checking knowledge base: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def main():
    """Entry point."""
    print("Checking Knowledge Base Content")
    print("==============================\n")
    check_knowledge_base()

if __name__ == "__main__":
    main() 