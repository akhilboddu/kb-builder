from fastapi import Depends
from ..services.crawler import CrawlerService
from ..services.document import DocumentService
from ..services.knowledge_base import KnowledgeBaseService
import os
from typing import Generator
import chromadb
from chromadb.config import Settings
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Get environment variables
CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en")
WEB_CRAWLER_API = os.getenv("WEB_CRAWLER_API", "https://web-crawler-ui07.onrender.com/crawl")
MAX_PAGES_DEFAULT = int(os.getenv("MAX_PAGES_DEFAULT", "50"))
MAX_DEPTH_DEFAULT = int(os.getenv("MAX_DEPTH_DEFAULT", "3"))

# Initialize ChromaDB client
def get_chroma_client() -> Generator:
    client = chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=CHROMA_PERSIST_DIRECTORY
    ))
    try:
        yield client
    finally:
        # No explicit cleanup needed for ChromaDB client
        pass

# Service dependencies
def get_kb_service(chroma_client: chromadb.Client = Depends(get_chroma_client)) -> KnowledgeBaseService:
    """Get the knowledge base service."""
    return KnowledgeBaseService(
        chroma_client=chroma_client,
        embedding_model=EMBEDDING_MODEL
    )

def get_crawler_service(kb_service: KnowledgeBaseService = Depends(get_kb_service)) -> CrawlerService:
    """Get the crawler service."""
    return CrawlerService(
        kb_service=kb_service,
        crawler_api_url=WEB_CRAWLER_API,
        max_pages_default=MAX_PAGES_DEFAULT,
        max_depth_default=MAX_DEPTH_DEFAULT
    )

def get_document_service(kb_service: KnowledgeBaseService = Depends(get_kb_service)) -> DocumentService:
    """Get the document service."""
    return DocumentService(kb_service=kb_service) 