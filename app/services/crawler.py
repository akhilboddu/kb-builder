"""
Service for processing web crawler data.
"""
import logging
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from datetime import datetime

from app.db.vector_store import add_chunks_to_vector_store, get_vector_store
from app.utils.text_processing import split_text_into_chunks
from app.models.crawler import PageContent


logger = logging.getLogger(__name__)


class CrawlerService:
    """Service for managing web crawler operations."""
    
    def __init__(self):
        """Initialize the crawler service."""
        pass
    
    async def process_data(self, data: Dict[str, Any]) -> str:
        """
        Process crawler data and add to knowledge base.
        
        Args:
            data: The crawler response data
            
        Returns:
            task_id: ID of the processed task
        """
        try:
            # Extract task ID
            task_id = data.get("task_id", "unknown")
            source_name = data.get("source_name", "web-crawler")
            
            # Extract pages
            pages = data.get("pages", [])
            logger.info(f"Processing {len(pages)} pages from task {task_id}")
            
            # Process each page
            for page in pages:
                await self.process_page(page, source=source_name)
                
            return task_id
            
        except Exception as e:
            logger.error(f"Error processing crawler data: {str(e)}")
            raise
    
    async def process_page(self, page: Dict[str, Any], source: str) -> None:
        """
        Process content from a single page.
        
        Args:
            page: The page data
            source: Source identifier
        """
        try:
            # Extract page data
            url = page.get("url", "")
            title = page.get("title", "")
            content = page.get("content", "")
            html = page.get("html", "")
            
            if not content and html:
                # Extract text from HTML if content is not provided
                soup = BeautifulSoup(html, "html.parser")
                content = soup.get_text(separator=" ", strip=True)
            
            if not content:
                logger.warning(f"No content found for page {url}")
                return
                
            # Create page content object
            page_content = PageContent(
                url=url,
                title=title,
                content=content,
                html=None,  # Don't store raw HTML in the knowledge base
                headings=page.get("headings", []),
                links=page.get("links", []),
                crawled_at=datetime.now()
            )
            
            # Split content into chunks
            chunks = split_text_into_chunks(
                content=page_content.content,
                title=page_content.title
            )
            
            # Add metadata to chunks
            chunks_with_metadata = []
            for i, chunk in enumerate(chunks):
                chunks_with_metadata.append({
                    "content": chunk,
                    "metadata": {
                        "source": source,
                        "url": url,
                        "title": title,
                        "chunk_index": i,
                        "type": "web"
                    }
                })
            
            # Add chunks to vector store
            await add_chunks_to_vector_store(chunks_with_metadata)
            
            logger.info(f"Processed page {url} with {len(chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Error processing page {page.get('url', 'unknown')}: {str(e)}")
            raise


# Service instance
_crawler_service = None


def get_crawler_service() -> CrawlerService:
    """Get the crawler service instance."""
    global _crawler_service
    if _crawler_service is None:
        _crawler_service = CrawlerService()
    return _crawler_service


# For backward compatibility
async def process_crawler_data(data: Dict[str, Any]) -> str:
    """Legacy function for processing crawler data."""
    service = get_crawler_service()
    return await service.process_data(data)


async def process_page_content(page: Dict[str, Any], source: str) -> None:
    """Legacy function for processing page content."""
    service = get_crawler_service()
    return await service.process_page(page, source)