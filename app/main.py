"""
Main application entry point for the Knowledge Base Builder.
"""
import os
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import dotenv
from datetime import datetime
from .api.routes import crawl, documents, knowledge_base
from .api.routes.knowledge_base import search as kb_search
from .db.document_repository import create_tables
from .models.knowledge_base import KnowledgeBaseStats

# Load environment variables
dotenv.load_dotenv()

# App settings
debug = os.getenv("DEBUG", "true").lower() == "true"
app_name = os.getenv("APP_NAME", "Knowledge Base Builder")

# Initialize FastAPI app
app = FastAPI(
    title=app_name,
    description="API for building structured knowledge bases from web crawler data and PDF documents.",
    version="0.1.0",
    debug=debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Add startup event to create database tables
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on app startup."""
    await create_tables()

# Include API routes
app.include_router(knowledge_base.router, prefix="/api/knowledge-base")
app.include_router(documents.router, prefix="/api/documents")
app.include_router(crawl.router, prefix="/api/crawl")

# Add health check endpoint
@app.get("/api/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# Frontend routes removed

# Search redirect endpoint removed

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled exceptions."""
    import traceback
    error_detail = f"{exc.__class__.__name__}: {str(exc)}" if debug else "Internal Server Error"
    if debug:
        print(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": error_detail, "success": False},
    )

# Root endpoint removed

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 