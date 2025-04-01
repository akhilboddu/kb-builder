"""
API routes for knowledge base operations.
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Path, Depends
from pydantic import BaseModel
from datetime import datetime

from app.models.knowledge_base import (
    SearchRequest, 
    SearchResponse, 
    KnowledgeBaseStats,
    ReindexResponse,
    SearchResult
)
from app.services.knowledge_base import search_knowledge_base, get_stats, reindex_kb, export_kb, get_kb_service, get_entry, list_entries
from app.services.knowledge_base import KnowledgeBaseService, delete_entry
from app.db.vector_store import search_vector_store, count_total_documents, count_items_by_metadata


router = APIRouter(tags=["Knowledge Base"])
logger = logging.getLogger(__name__)


@router.get("/kb-stats", response_model=KnowledgeBaseStats)
async def kb_stats():
    """
    Get knowledge base statistics.
    
    Returns:
        KnowledgeBaseStats with statistics
    """
    try:
        return await get_stats()
    except Exception as e:
        logger.error(f"Error getting KB stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")


@router.get("/search", response_model=SearchResponse)
async def search(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Number of results to return"),
    filter_category: str = Query(None, description="Filter by category"),
    filter_source: str = Query(None, description="Filter by source"),
    filter_knowledge_base_id: str = Query(None, description="Filter by knowledge base ID")
):
    """
    Search the knowledge base.
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        filter_category: Optional category filter
        filter_source: Optional source filter
        filter_knowledge_base_id: Optional knowledge base ID filter
        
    Returns:
        SearchResponse with search results
    """
    try:
        # Create filters dict
        filters = {}
        if filter_category:
            filters["category"] = filter_category
        if filter_source:
            filters["source"] = filter_source
        if filter_knowledge_base_id:
            filters["knowledge_base_id"] = filter_knowledge_base_id
            logger.info(f"Filtering search by knowledge_base_id: {filter_knowledge_base_id}")
        
        # Get the KB service    
        kb_service = get_kb_service()
        
        logger.info(f"Searching with query: '{query}', filters: {filters}")
        
        # Use the vector store directly for more control
        results = await search_vector_store(
            query=query,
            filter_conditions=filters,
            limit=limit
        )
        
        logger.info(f"Search returned {len(results)} results")
        
        # Log first result's metadata for debugging
        if results and len(results) > 0 and "metadata" in results[0]:
            logger.info(f"First result metadata: {results[0]['metadata']}")
        
        # Convert to SearchResult objects
        search_results = []
        for result in results:
            # Get values from the result dict
            document = result.get("document", "")
            metadata = result.get("metadata", {})
            score = result.get("score", 0.0)
            result_id = result.get("id", "")
            
            # Determine source based on metadata
            source = None
            if metadata.get("type") == "web":
                source = metadata.get("url")
            elif metadata.get("type") == "pdf":
                source = f"{metadata.get('title')} (Page {metadata.get('page_number')})"
            else:
                source = metadata.get("source", "Unknown")
            
            search_results.append(
                SearchResult(
                    id=result_id,
                    content=document,
                    metadata=metadata,
                    score=score,
                    source=source
                )
            )
        
        return SearchResponse(
            query=query,
            results=search_results,
            count=len(search_results)
        )
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


# Adding POST endpoint to match PLANNING.md
@router.post("/", response_model=dict)
async def add_content(content: dict):
    """
    Add content to knowledge base.
    
    Args:
        content: Content to add to knowledge base
        
    Returns:
        Dictionary with status
    """
    try:
        # Use the knowledge base service to add content
        kb_service = get_kb_service()
        return await kb_service.add_content(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding content: {str(e)}")


# Adding a GET endpoint to list all knowledge base entries
# This must be BEFORE the /{entry_id} endpoint to avoid route conflicts
@router.get("/entries", response_model=List[Dict[str, Any]])
async def list_knowledge_base_entries(
    limit: int = Query(10, description="Maximum number of entries to return", ge=1, le=100),
    offset: int = Query(0, description="Number of entries to skip", ge=0),
    filter_category: Optional[str] = Query(None, description="Filter by category"),
    filter_source: Optional[str] = Query(None, description="Filter by source"),
    knowledge_base_id: Optional[str] = Query(None, description="Filter by knowledge base ID"),
    debug: bool = Query(False, description="Include debug information in response")
):
    """
    List all knowledge base entries with pagination and filtering.
    
    Args:
        limit: Maximum number of entries to return (1-100)
        offset: Number of entries to skip for pagination
        filter_category: Optional filter by category
        filter_source: Optional filter by source
        knowledge_base_id: Optional filter by knowledge base ID
        debug: Include debug information in response
        
    Returns:
        List of knowledge base entries
    """
    try:
        # Create filters dictionary with proper string conversion
        filters = {}
        if filter_category:
            filters["category"] = filter_category
        if filter_source:
            filters["source"] = filter_source
        if knowledge_base_id:
            filters["knowledge_base_id"] = knowledge_base_id
            logger.info(f"Filtering entries by knowledge_base_id: {knowledge_base_id}")
            
        logger.info(f"Listing knowledge base entries with limit={limit}, offset={offset}, filters={filters}")
            
        # Get entries from the knowledge base service
        # Pass correct limit and offset instead of fetching all and filtering later
        entries = await list_entries(
            limit=limit,
            offset=offset,
            filters=filters
        )
        
        logger.info(f"Found {len(entries)} entries")
        
        # Log first entry's metadata for debugging
        if entries and len(entries) > 0 and "metadata" in entries[0]:
            logger.info(f"First entry metadata: {entries[0]['metadata']}")
        
        # Add debug information if requested
        if debug:
            # Get all stats using the same method as the stats endpoint for consistency
            stats = await get_stats()
            
            # Get all knowledge base IDs from the entries for debugging
            kb_ids = set()
            for entry in entries:
                if "metadata" in entry and "knowledge_base_id" in entry["metadata"]:
                    kb_ids.add(entry["metadata"]["knowledge_base_id"])
            
            return [
                {
                    "debug_info": {
                        "total_documents": stats.total_documents,
                        "total_entries": stats.total_entries,
                        "entries_found": len(entries),
                        "knowledge_bases": stats.knowledge_bases,
                        "knowledge_base_ids_in_results": list(kb_ids),
                        "applied_filters": filters
                    }
                },
                *entries
            ]
        
        return entries
        
    except Exception as e:
        logger.error(f"Error listing knowledge base entries: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error listing knowledge base entries: {str(e)}"
        )


# Adding GET endpoint for specific entry
@router.get("/{entry_id}", response_model=dict)
async def get_entry_endpoint(entry_id: str):
    """
    Get knowledge base entry by ID.
    
    Args:
        entry_id: Entry ID to retrieve
        
    Returns:
        Knowledge base entry with content and metadata
    """
    try:
        # Get the entry from the knowledge base service
        entry = await get_entry(entry_id)
        
        if entry is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Entry with ID {entry_id} not found"
            )
            
        return entry
        
    except HTTPException:
        # Re-raise HTTPExceptions (like 404)
        raise
        
    except Exception as e:
        logger.error(f"Error retrieving entry {entry_id}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving entry: {str(e)}"
        )


# Adding DELETE endpoint for specific entry
@router.delete("/{entry_id}", response_model=dict)
async def delete_entry_endpoint(entry_id: str):
    """
    Delete knowledge base entry.
    
    Args:
        entry_id: Entry ID to delete
        
    Returns:
        Status message
    """
    try:
        # Use the knowledge base service to delete the entry
        result = await delete_entry(entry_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting entry: {str(e)}")


@router.post("/reindex", response_model=ReindexResponse)
async def reindex(background_tasks: BackgroundTasks):
    """
    Regenerate embeddings for all content.
    
    Args:
        background_tasks: FastAPI background tasks
        
    Returns:
        ReindexResponse with status
    """
    # Start reindexing in the background
    background_tasks.add_task(reindex_kb)
    
    return ReindexResponse(
        status="processing",
        message="Reindexing started"
    ) 