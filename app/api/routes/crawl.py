"""
API routes for web crawler integration.
"""
from typing import Dict, Any, List, Optional
import uuid
import json
from fastapi import APIRouter, HTTPException, BackgroundTasks
import httpx
from pydantic import BaseModel, HttpUrl
from datetime import datetime

from app.core.config import settings
from app.services.crawler import process_crawler_data
from app.models.crawler import CrawlRequest, CrawlResponse, CustomCrawlData


router = APIRouter(tags=["Crawl"])


# Helper function to create mock data for local testing when external crawler is down
def generate_mock_crawler_data(url: str, max_pages: int = 3, max_depth: int = 2) -> Dict[str, Any]:
    """
    Generate mock crawler data for testing purposes.
    
    Args:
        url: The URL that would have been crawled
        max_pages: Maximum number of pages
        max_depth: Maximum crawl depth
        
    Returns:
        Dict with mock crawler data
    """
    task_id = f"mock-{uuid.uuid4()}"
    current_time = datetime.now().isoformat()
    
    # Create some sample pages with mock content
    pages = []
    base_url = str(url).rstrip('/')
    
    # Mock homepage
    pages.append({
        "url": base_url,
        "title": f"Homepage - {base_url.split('//')[1]}",
        "content": f"This is a mock homepage content for {base_url} generated for testing purposes.",
        "links": [f"{base_url}/about", f"{base_url}/products", f"{base_url}/contact"],
        "headings": ["Welcome", "Features", "Get Started"],
        "crawled_at": current_time
    })
    
    # Mock about page
    pages.append({
        "url": f"{base_url}/about",
        "title": f"About Us - {base_url.split('//')[1]}",
        "content": f"This is a mock about page content. Our company provides amazing services and products. Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
        "links": [f"{base_url}", f"{base_url}/team", f"{base_url}/contact"],
        "headings": ["About Us", "Our Mission", "Our Team"],
        "crawled_at": current_time
    })
    
    # Mock products page
    pages.append({
        "url": f"{base_url}/products",
        "title": f"Products - {base_url.split('//')[1]}",
        "content": f"This is a mock products page content. We offer various high-quality products. Sed ut perspiciatis unde omnis iste natus error sit voluptatem.",
        "links": [f"{base_url}", f"{base_url}/products/1", f"{base_url}/products/2"],
        "headings": ["Our Products", "Featured Items", "Pricing"],
        "crawled_at": current_time
    })
    
    return {
        "task_id": task_id,
        "source_name": f"mock-crawler-{base_url.split('//')[1]}",
        "url": base_url,
        "status": "completed",
        "pages": pages[:max_pages],
        "stats": {
            "pages_crawled": len(pages[:max_pages]),
            "max_depth": max_depth,
            "start_time": current_time,
            "end_time": current_time
        }
    }


# @router.post("/", response_model=CrawlResponse)
# async def crawl_website(request: CrawlRequest, background_tasks: BackgroundTasks):
#     """
#     Initiate a web crawling task.
#     
#     Args:
#         request: The crawl request with URL and parameters
#         background_tasks: FastAPI background tasks
#         
#     Returns:
#         CrawlResponse with task ID and status
#     """
#     try:
#         # Log the request for debugging
#         print(f"Attempting to crawl: {request.url} with max_depth={request.max_depth or settings.MAX_DEPTH_DEFAULT}")
#         
#         # Use a shorter timeout to fail faster if the service is down
#         async with httpx.AsyncClient(timeout=10.0) as client:
#             try:
#                 response = await client.post(
#                     settings.WEB_CRAWLER_API,
#                     json={
#                         "url": str(request.url),
#                         "max_pages": request.max_pages or settings.MAX_PAGES_DEFAULT,
#                         "max_depth": request.max_depth or settings.MAX_DEPTH_DEFAULT
#                     }
#                 )
#                 
#                 if response.status_code != 200:
#                     error_detail = f"Crawler API error: Status code {response.status_code}"
#                     try:
#                         error_detail += f", Response: {response.text}"
#                     except:
#                         pass
#                     
#                     # If external API fails, use the mock data instead
#                     print(f"External crawler API failed: {error_detail}. Using mock data instead.")
#                     data = generate_mock_crawler_data(
#                         url=str(request.url),
#                         max_pages=request.max_pages or settings.MAX_PAGES_DEFAULT,
#                         max_depth=request.max_depth or settings.MAX_DEPTH_DEFAULT
#                     )
#                 else:
#                     data = response.json()
#                 
#                 task_id = data.get("task_id", "unknown")
#                 
#                 # Process the crawler data in the background
#                 background_tasks.add_task(process_crawler_data, data)
#                 
#                 return CrawlResponse(
#                     task_id=task_id,
#                     status="processing",
#                     message="Crawling started successfully"
#                 )
#                 
#             except httpx.RequestError as e:
#                 # Provide more details about the connection error
#                 error_message = f"Cannot connect to crawler service at {settings.WEB_CRAWLER_API}: {str(e)}"
#                 print(error_message)
#                 
#                 # Use mock data as fallback
#                 print("Using mock crawler data as fallback")
#                 mock_data = generate_mock_crawler_data(
#                     url=str(request.url),
#                     max_pages=request.max_pages or settings.MAX_PAGES_DEFAULT,
#                     max_depth=request.max_depth or settings.MAX_DEPTH_DEFAULT
#                 )
#                 task_id = mock_data.get("task_id", "mock-fallback")
#                 
#                 # Process the mock data in the background
#                 background_tasks.add_task(process_crawler_data, mock_data)
#                 
#                 return CrawlResponse(
#                     task_id=task_id,
#                     status="processing",
#                     message="Using mock data (crawler service unavailable)"
#                 )
#     
#     except Exception as e:
#         if not isinstance(e, HTTPException):
#             print(f"Unexpected error in crawl_website: {str(e)}")
#             raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
#         raise


# @router.get("/", response_model=List[Dict[str, Any]])
# async def list_crawl_jobs():
#     """
#     List all crawl jobs.
#     
#     Returns:
#         List of crawl jobs with status
#     """
#     try:
#         # In a real implementation, this would query a database or task queue
#         # For now, return a placeholder response
#         return [
#             {
#                 "task_id": "example-task-1",
#                 "url": "https://example.com",
#                 "status": "completed",
#                 "created_at": "2023-05-01T12:00:00Z"
#             },
#             {
#                 "task_id": "example-task-2",
#                 "url": "https://example.org",
#                 "status": "processing",
#                 "created_at": "2023-05-01T13:00:00Z"
#             }
#         ]
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error listing crawl jobs: {str(e)}")


# @router.post("/custom", response_model=CrawlResponse)
# async def process_custom_crawl_data(data: CustomCrawlData, background_tasks: BackgroundTasks):
#     """
#     Process custom crawler output.
#     
#     Args:
#         data: Custom crawler data in compatible format
#         background_tasks: FastAPI background tasks
#         
#     Returns:
#         CrawlResponse with status
#     """
#     try:
#         # Process the custom crawler data in the background
#         background_tasks.add_task(process_crawler_data, data.dict())
#         
#         return CrawlResponse(
#             task_id=data.source_id,
#             status="processing",
#             message="Custom crawler data processing started"
#         )
#         
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"Error processing custom crawler data: {str(e)}")


# @router.get("/{task_id}", response_model=CrawlResponse)
# async def get_crawl_status(task_id: str):
#     """
#     Get the status of a crawl task.
#     
#     Args:
#         task_id: The task ID to check
#         
#     Returns:
#         CrawlResponse with current status
#     """
#     # In a real implementation, this would check a database or task queue
#     # For now, we'll return a placeholder
#     return CrawlResponse(
#         task_id=task_id,
#         status="completed",  # Placeholder
#         message="Task status retrieved"
#     ) 