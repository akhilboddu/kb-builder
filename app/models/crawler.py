"""
Data models for web crawler functionality.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
import uuid


class CrawlRequest(BaseModel):
    """Request model for initiating web crawling."""
    url: HttpUrl = Field(..., description="URL to crawl")
    max_pages: Optional[int] = Field(None, description="Maximum number of pages to crawl")
    max_depth: Optional[int] = Field(None, description="Maximum depth to crawl")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com",
                "max_pages": 50,
                "max_depth": 3
            }
        }


class CrawlResponse(BaseModel):
    """Response model for crawl operations."""
    task_id: str = Field(..., description="Task ID for tracking")
    status: str = Field(..., description="Status of the crawl task")
    message: str = Field(..., description="Descriptive message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "fbd8a034-8d9e-4a93-b814-b3a3f3e5f254",
                "status": "processing",
                "message": "Crawling started successfully"
            }
        }


class PageContent(BaseModel):
    """Model for page content from crawler."""
    url: str
    title: str
    content: str
    html: Optional[str] = None
    headings: Optional[List[Dict[str, Any]]] = None
    links: Optional[List[str]] = None
    crawled_at: Optional[datetime] = None


class CustomCrawlData(BaseModel):
    """Model for custom crawler data."""
    source_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_name: str
    pages: List[PageContent]
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_id": "custom-12345",
                "source_name": "My Custom Crawler",
                "pages": [
                    {
                        "url": "https://example.com",
                        "title": "Example Domain",
                        "content": "This domain is for use in illustrative examples in documents.",
                        "headings": [
                            {"level": 1, "text": "Example Domain"}
                        ],
                        "links": [
                            "https://www.iana.org/domains/example"
                        ]
                    }
                ]
            }
        } 