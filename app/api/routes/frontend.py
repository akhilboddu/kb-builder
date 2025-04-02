from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import chromadb
from chromadb.config import Settings
from ..dependencies import get_crawler_service, get_document_service, get_kb_service
from ...services.crawler import CrawlerService
from ...services.document import DocumentService
from ...services.knowledge_base import KnowledgeBaseService

# Set up templates
templates_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates")
templates = Jinja2Templates(directory=templates_path)

router = APIRouter(tags=["frontend"])

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the home page"""
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    kb_service: KnowledgeBaseService = Depends(get_kb_service),
    crawler_service: CrawlerService = Depends(get_crawler_service),
    document_service: DocumentService = Depends(get_document_service)
):
    """Render the dashboard page with ChromaDB collections"""
    try:
        # Get ChromaDB collections
        collections = kb_service.list_collections()
        
        # Get statistics
        stats = {
            "total_collections": len(collections),
            "total_documents": sum(c.count for c in collections) if collections else 0,
            "crawler_jobs": len(crawler_service.list_jobs()),
            "pdf_documents": len(document_service.list_documents())
        }
        
        return templates.TemplateResponse(
            "dashboard.html", 
            {
                "request": request, 
                "collections": collections,
                "stats": stats
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/crawl", response_class=HTMLResponse)
async def crawl_page(request: Request, crawler_service: CrawlerService = Depends(get_crawler_service)):
    """Render the web crawler page"""
    try:
        # Get active and completed crawler jobs
        all_jobs = crawler_service.list_jobs()
        active_jobs = [job for job in all_jobs if job.status in ["in_progress", "pending"]]
        completed_jobs = [job for job in all_jobs if job.status in ["completed", "failed", "cancelled"]]
        
        # Add status colors for UI
        for job in active_jobs + completed_jobs:
            if job.status == "in_progress":
                job.status_color = "primary"
            elif job.status == "pending":
                job.status_color = "secondary"
            elif job.status == "completed":
                job.status_color = "success"
            elif job.status == "failed":
                job.status_color = "danger"
            elif job.status == "cancelled":
                job.status_color = "warning"
        
        return templates.TemplateResponse(
            "crawl.html", 
            {
                "request": request, 
                "active_jobs": active_jobs,
                "completed_jobs": completed_jobs
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents", response_class=HTMLResponse)
async def documents_page(request: Request, document_service: DocumentService = Depends(get_document_service)):
    """Render the document management page"""
    try:
        # Get documents
        documents = document_service.list_documents()
        
        return templates.TemplateResponse(
            "documents.html", 
            {
                "request": request, 
                "documents": documents
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_class=HTMLResponse)
async def search_page(
    request: Request, 
    query: str = None,
    collection_name: str = None,
    limit: int = 10,
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """Render the search page"""
    try:
        # Get collections for dropdown
        collections = kb_service.list_collections()
        
        # Get search results if query provided
        results = []
        if query:
            results = kb_service.search(query, collection_name, limit)
        
        return templates.TemplateResponse(
            "search.html", 
            {
                "request": request,
                "collections": collections,
                "query": query,
                "collection_name": collection_name,
                "limit": limit,
                "results": results
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/collection/{collection_name}", response_class=HTMLResponse)
async def collection_page(
    request: Request,
    collection_name: str,
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """Render a collection details page"""
    try:
        # Get collection details
        collection = kb_service.get_collection(collection_name)
        
        # Get collection items (first 100)
        items = kb_service.get_collection_items(collection_name, limit=100)
        
        return templates.TemplateResponse(
            "collection.html", 
            {
                "request": request,
                "collection": collection,
                "items": items
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/collection/{collection_name}/search", response_class=HTMLResponse)
async def collection_search_page(
    request: Request,
    collection_name: str,
    query: str = None,
    limit: int = 10,
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """Render a collection-specific search page"""
    try:
        # Get collection details
        collection = kb_service.get_collection(collection_name)
        
        # Get search results if query provided
        results = []
        if query:
            results = kb_service.search(query, collection_name, limit)
        
        return templates.TemplateResponse(
            "collection_search.html", 
            {
                "request": request,
                "collection": collection,
                "query": query,
                "limit": limit,
                "results": results
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{document_id}", response_class=HTMLResponse)
async def document_page(
    request: Request,
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """Render a document details page"""
    try:
        # Get document details
        document = document_service.get_document(document_id)
        
        # Get document chunks
        chunks = document_service.get_document_chunks(document_id)
        
        return templates.TemplateResponse(
            "document.html", 
            {
                "request": request,
                "document": document,
                "chunks": chunks
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/crawl/{job_id}", response_class=HTMLResponse)
async def crawl_job_page(
    request: Request,
    job_id: str,
    crawler_service: CrawlerService = Depends(get_crawler_service)
):
    """Render a crawl job details page"""
    try:
        # Get job details
        job = crawler_service.get_job(job_id)
        
        # Add status color for UI
        if job.status == "in_progress":
            job.status_color = "primary"
        elif job.status == "pending":
            job.status_color = "secondary"
        elif job.status == "completed":
            job.status_color = "success"
        elif job.status == "failed":
            job.status_color = "danger"
        elif job.status == "cancelled":
            job.status_color = "warning"
        
        return templates.TemplateResponse(
            "crawl_job.html", 
            {
                "request": request,
                "job": job
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 