"""
Service for knowledge base operations.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from app.db.vector_store import (
    get_vector_store,
    search_vector_store,
    count_items_by_metadata,
    add_chunks_to_vector_store,
    get_documents_by_metadata,
    get_all_documents,
    count_total_documents
)
from app.models.knowledge_base import SearchResult, KnowledgeBaseStats


logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """Service for managing knowledge base operations."""
    
    def __init__(self):
        """Initialize the knowledge base service."""
        pass
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search the knowledge base.
        
        Args:
            query: Search query
            limit: Maximum number of results
            filters: Optional metadata filters
            
        Returns:
            List of search results
        """
        try:
            # Search the vector store
            results = await search_vector_store(
                query=query,
                filter_conditions=filters,
                limit=limit
            )
            
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
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            raise
    
    async def add_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add content to the knowledge base.
        
        Args:
            content: Content to add to the knowledge base, could be web crawler data or other structured data
            
        Returns:
            Dictionary with status information
        """
        try:
            # Generate a unique ID if not provided
            content_id = content.get("id", f"kb-{str(uuid.uuid4())}")
            
            # Get knowledge_base_id or use default
            knowledge_base_id = content.get("knowledge_base_id", "default-kb")
            
            # Log the knowledge base ID being used
            logger.info(f"Adding content with knowledge_base_id: '{knowledge_base_id}'")
            
            # Process based on content type
            if "pages" in content and isinstance(content["pages"], list):
                # Handle web crawler data
                logger.info(f"Processing {len(content['pages'])} pages from crawler data")
                
                chunks = []
                for page in content["pages"]:
                    url = page.get("url", "")
                    title = page.get("title", "No title")
                    
                    # Create content from paragraphs or combine headings and paragraphs
                    paragraphs = page.get("paragraphs", [])
                    headings = page.get("headings", [])
                    
                    if paragraphs:
                        # Split paragraphs into chunks (simple approach)
                        for i, paragraph in enumerate(paragraphs):
                            if not paragraph.strip():
                                continue
                                
                            # Include relevant heading if available
                            heading_idx = min(i, len(headings) - 1) if headings else -1
                            heading_text = headings[heading_idx] if heading_idx >= 0 else ""
                            
                            # Create chunk with metadata
                            chunk = {
                                "content": f"{heading_text}\n\n{paragraph}" if heading_text else paragraph,
                                "metadata": {
                                    "document_id": content_id,
                                    "knowledge_base_id": knowledge_base_id,
                                    "url": url,
                                    "title": title,
                                    "type": "web",
                                    "source": content.get("base_url", url),
                                    "category": "web_content",
                                    "chunk_index": i,
                                    "creation_date": datetime.now().isoformat()
                                }
                            }
                            chunks.append(chunk)
                    else:
                        # If no paragraphs, use headings as content
                        for i, heading in enumerate(headings):
                            if not heading.strip():
                                continue
                                
                            chunk = {
                                "content": heading,
                                "metadata": {
                                    "document_id": content_id,
                                    "knowledge_base_id": knowledge_base_id,
                                    "url": url,
                                    "title": title,
                                    "type": "web",
                                    "source": content.get("base_url", url),
                                    "category": "web_content",
                                    "chunk_index": i,
                                    "creation_date": datetime.now().isoformat()
                                }
                            }
                            chunks.append(chunk)
                
                # Log a sample chunk metadata
                if chunks and len(chunks) > 0:
                    logger.info(f"Sample chunk metadata: {chunks[0]['metadata']}")
                
                # Add chunks to vector store
                if chunks:
                    await add_chunks_to_vector_store(chunks)
                    logger.info(f"Added {len(chunks)} chunks to knowledge base from crawler data")
                    return {
                        "entry_id": content_id,
                        "knowledge_base_id": knowledge_base_id,
                        "status": "added",
                        "message": f"Content added to knowledge base ({len(chunks)} chunks)"
                    }
                else:
                    logger.warning("No content chunks extracted from crawler data")
                    return {
                        "entry_id": content_id,
                        "knowledge_base_id": knowledge_base_id,
                        "status": "warning",
                        "message": "No content chunks extracted from crawler data"
                    }
            else:
                # For other content types, use a simple approach
                chunk = {
                    "content": str(content.get("content", "")),
                    "metadata": {
                        "document_id": content_id,
                        "knowledge_base_id": knowledge_base_id,
                        "type": content.get("type", "custom"),
                        "source": content.get("source", "api"),
                        "category": content.get("category", "custom_content"),
                        "creation_date": datetime.now().isoformat()
                    }
                }
                
                # Log metadata
                logger.info(f"Custom content metadata: {chunk['metadata']}")
                
                # Ensure knowledge_base_id is properly formatted as a string
                chunk["metadata"]["knowledge_base_id"] = str(knowledge_base_id)
                
                await add_chunks_to_vector_store([chunk])
                logger.info("Added custom content to knowledge base")
                return {
                    "entry_id": content_id,
                    "knowledge_base_id": knowledge_base_id,
                    "status": "added",
                    "message": "Content added to knowledge base"
                }
                
        except Exception as e:
            logger.error(f"Error adding content to knowledge base: {str(e)}")
            raise
    
    async def get_stats(self) -> KnowledgeBaseStats:
        """
        Get knowledge base statistics.
        
        Returns:
            KnowledgeBaseStats object
        """
        try:
            # Get document count by type
            pdf_documents = await count_items_by_metadata(filter_key="type", filter_value="pdf")
            web_documents = await count_items_by_metadata(filter_key="type", filter_value="web")
            
            # Get category counts
            categories = await count_items_by_metadata(filter_key="category")
            if not isinstance(categories, dict):
                categories = {}
            
            # Get source counts
            sources = await count_items_by_metadata(filter_key="source")
            if not isinstance(sources, dict):
                sources = {}
            
            # Get knowledge base counts
            knowledge_bases = await count_items_by_metadata(filter_key="knowledge_base_id", count_unique=True)
            if not isinstance(knowledge_bases, dict):
                knowledge_bases = {"default-kb": 0}
            
            # Get page count for PDFs
            total_pages_data = await count_items_by_metadata(filter_key="page_number", count_unique=True)
            
            # Handle total_pages properly
            total_pages = 0
            if isinstance(total_pages_data, dict):
                total_pages = len(total_pages_data)
            elif isinstance(total_pages_data, int):
                total_pages = total_pages_data
            
            # Get total chunks
            total_chunks = pdf_documents + web_documents
            
            # Get total documents using count_total_documents() for consistency with debug view
            total_documents = await count_total_documents()
            
            # Get total entries by counting unique document IDs
            document_ids = await count_items_by_metadata(filter_key="document_id", count_unique=True)
            total_entries = len(document_ids) if isinstance(document_ids, dict) else 0
            
            logger.info(f"Stats calculation: total_documents={total_documents}, total_entries={total_entries}")
            
            return KnowledgeBaseStats(
                total_documents=total_documents,
                total_entries=total_entries,
                total_pages=total_pages,
                total_chunks=total_chunks,
                by_source=sources,
                by_category=categories,
                knowledge_bases=knowledge_bases,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error getting knowledge base stats: {str(e)}")
            raise
    
    async def reindex(self) -> None:
        """
        Regenerate all embeddings in the knowledge base.
        """
        try:
            # Get vector store
            vector_store = await get_vector_store()
            
            # In a real implementation, this would extract all documents
            # and regenerate embeddings with a potentially new model
            logger.info("Reindexing knowledge base started")
            
            # Add more detailed logs to verify operation
            doc_count = await count_total_documents()
            logger.info(f"Reindexing {doc_count} documents in knowledge base")
            
            # Get all documents that would be reindexed
            all_docs = await get_all_documents(limit=1000, offset=0)
            unique_ids = set()
            for doc in all_docs:
                if doc.get("metadata", {}).get("document_id"):
                    unique_ids.add(doc["metadata"]["document_id"])
            
            logger.info(f"Found {len(unique_ids)} unique document IDs for reindexing")
            
            # In a real implementation, we would regenerate embeddings here
            # Placeholder for actual reindexing logic
            
            logger.info("Reindexing knowledge base completed")
            
        except Exception as e:
            logger.error(f"Error reindexing knowledge base: {str(e)}")
            raise
    
    async def export(self) -> Dict[str, Any]:
        """
        Export knowledge base data.
        
        Returns:
            Dict with exported data
        """
        try:
            # Get vector store
            vector_store = await get_vector_store()
            
            # In a real implementation, this would extract all documents and metadata
            
            # Get stats for basic info
            stats = await self.get_stats()
            
            # For now, return a placeholder with stats
            return {
                "stats": stats.dict(),
                "exported_at": datetime.now().isoformat(),
                "format_version": "0.1.0"
                # In a real implementation, "documents" would be included with actual content
            }
            
        except Exception as e:
            logger.error(f"Error exporting knowledge base: {str(e)}")
            raise
    
    async def get_collection_items(self, collection_name: str):
        """
        Get all items from a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            List of items with embeddings and metadata
        """
        try:
            # Get vector store
            vector_store = await get_vector_store()
            
            # Get all items from the collection
            items = await vector_store.get(
                where={"collection": collection_name}
            )
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting collection items: {str(e)}")
            raise
            
    async def get_entry(self, entry_id: str) -> Dict[str, Any]:
        """
        Get a specific knowledge base entry by ID.
        
        Args:
            entry_id: ID of the entry to retrieve
            
        Returns:
            Dictionary containing the entry data or None if not found
        """
        try:
            # Query for items with matching document_id in metadata
            results = await get_documents_by_metadata('document_id', entry_id)
            
            if not results or len(results) == 0:
                logger.warning(f"Entry with ID {entry_id} not found")
                return None
                
            # Combine all chunks into a single response
            chunks = []
            metadata = {}
            
            for item in results:
                chunks.append(item.get("document", ""))
                # Use metadata from the first chunk if not already set
                if not metadata and "metadata" in item:
                    metadata = item["metadata"]
            
            return {
                "entry_id": entry_id,
                "content": "\n\n".join(chunks),
                "metadata": metadata,
                "knowledge_base_id": metadata.get("knowledge_base_id", "default-kb")
            }
            
        except Exception as e:
            logger.error(f"Error retrieving entry {entry_id}: {str(e)}")
            raise
            
    async def delete_entry(self, entry_id: str) -> Dict[str, Any]:
        """
        Delete a knowledge base entry by ID.
        
        Args:
            entry_id: ID of the entry to delete
            
        Returns:
            Dictionary with status information
        """
        try:
            # First, check if the entry exists
            results = await get_documents_by_metadata('document_id', entry_id)
            
            if not results or len(results) == 0:
                logger.warning(f"Entry with ID {entry_id} not found for deletion")
                return {
                    "entry_id": entry_id,
                    "status": "error",
                    "message": f"Entry {entry_id} not found"
                }
            
            # Get vector store client and collection
            client, collection = await get_vector_store()
            
            # Get IDs of all chunks for this document
            chunk_ids = [result.get("id") for result in results if result.get("id")]
            
            if not chunk_ids:
                logger.warning(f"No chunk IDs found for entry {entry_id}")
                return {
                    "entry_id": entry_id,
                    "status": "error",
                    "message": f"No chunk IDs found for entry {entry_id}"
                }
            
            # Delete all chunks from the collection
            collection.delete(ids=chunk_ids)
            
            logger.info(f"Deleted entry {entry_id} ({len(chunk_ids)} chunks)")
            return {
                "entry_id": entry_id,
                "status": "deleted",
                "message": f"Entry {entry_id} deleted successfully ({len(chunk_ids)} chunks removed)"
            }
            
        except Exception as e:
            logger.error(f"Error deleting entry {entry_id}: {str(e)}")
            raise
            
    async def list_entries(
        self,
        limit: int = 10,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        List all knowledge base entries with pagination and filtering.
        
        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            filters: Optional metadata filters
            
        Returns:
            List of entry dictionaries
        """
        try:
            # Get documents from vector store with proper pagination
            # Pass limit and offset directly to the database query
            results = await get_all_documents(
                limit=limit * 5,  # Get more chunks to account for consolidation by document_id
                offset=offset,
                filter_conditions=filters
            )
            
            # Log the results for debugging
            logger.info(f"Retrieved {len(results)} documents from vector store with limit={limit*5}, offset={offset}")
            
            if not results:
                logger.warning("No documents found in get_all_documents call")
                # Try a different approach to get entries by document_id
                try:
                    # Get unique document_ids by using count_items_by_metadata
                    unique_doc_ids = await count_items_by_metadata(filter_key="document_id", count_unique=True)
                    logger.info(f"Found {len(unique_doc_ids)} unique document_ids: {list(unique_doc_ids.keys())[:5]} (showing up to 5)")
                    
                    # If we have document IDs but no results, try fetching each directly
                    if unique_doc_ids:
                        all_entries = []
                        doc_ids = list(unique_doc_ids.keys())
                        
                        # Filter document IDs by knowledge_base_id if specified
                        if filters and "knowledge_base_id" in filters:
                            kb_id = filters["knowledge_base_id"]
                            logger.info(f"Filtering doc_ids by knowledge_base_id: {kb_id}")
                            
                            # To filter by knowledge_base_id, we need to check each entry's metadata
                            filtered_doc_ids = []
                            for doc_id in doc_ids:
                                entry = await self.get_entry(doc_id)
                                if entry and entry.get("metadata") and entry["metadata"].get("knowledge_base_id") == kb_id:
                                    filtered_doc_ids.append(doc_id)
                            
                            logger.info(f"Filtered from {len(doc_ids)} to {len(filtered_doc_ids)} doc_ids")
                            doc_ids = filtered_doc_ids
                        
                        # Apply pagination to the doc_ids list
                        # Increase the limit to fetch more document IDs initially to ensure we find all entries
                        # then apply correct pagination
                        logger.info(f"Applying pagination: offset={offset}, limit={limit}, total doc_ids={len(doc_ids)}")
                        paginated_doc_ids = doc_ids[offset:offset+limit]
                        logger.info(f"After pagination: {len(paginated_doc_ids)} doc_ids selected")
                        
                        for doc_id in paginated_doc_ids:
                            entry = await self.get_entry(doc_id)
                            if entry:
                                # Ensure knowledge_base_id is included in the entry
                                if "metadata" in entry:
                                    entry["knowledge_base_id"] = entry["metadata"].get("knowledge_base_id", "default-kb")
                                all_entries.append(entry)
                        
                        logger.info(f"Retrieved {len(all_entries)} entries directly by ID")
                        return all_entries
                except Exception as e:
                    logger.error(f"Error trying fallback document retrieval: {str(e)}")
                
                return []
                
            # Group results by document_id to consolidate chunks
            entries_by_id = {}
            
            for item in results:
                metadata = item.get("metadata", {})
                doc_id = metadata.get("document_id")
                
                if not doc_id:
                    continue
                    
                if doc_id not in entries_by_id:
                    entries_by_id[doc_id] = {
                        "entry_id": doc_id,
                        "chunks": [],
                        "metadata": metadata
                    }
                
                entries_by_id[doc_id]["chunks"].append(item.get("document", ""))
            
            # Convert to list and add content
            entries = []
            for doc_id, entry_data in entries_by_id.items():
                metadata = entry_data["metadata"]
                # Ensure knowledge_base_id is included in the entry
                knowledge_base_id = metadata.get("knowledge_base_id", "default-kb")
                
                entries.append({
                    "entry_id": entry_data["entry_id"],
                    "knowledge_base_id": knowledge_base_id,
                    "content": "\n\n".join(entry_data["chunks"]),
                    "metadata": metadata
                })
            
            logger.info(f"Found {len(entries)} entries after grouping by document_id")
            
            # If we got more entries than the limit due to the multiplier, apply final pagination
            if len(entries) > limit:
                entries = entries[:limit]
                logger.info(f"Applied final limit to return {len(entries)} entries")
            
            return entries
            
        except Exception as e:
            logger.error(f"Error listing knowledge base entries: {str(e)}")
            raise


# Service instance
_kb_service = None


def get_kb_service() -> KnowledgeBaseService:
    """Get the knowledge base service instance."""
    global _kb_service
    if _kb_service is None:
        _kb_service = KnowledgeBaseService()
    return _kb_service


# For backward compatibility
async def search_knowledge_base(
    query: str,
    limit: int = 10,
    filters: Optional[Dict[str, Any]] = None
) -> List[SearchResult]:
    """Legacy function for searching knowledge base."""
    service = get_kb_service()
    return await service.search(query, limit, filters)


async def get_stats() -> KnowledgeBaseStats:
    """Legacy function for getting knowledge base stats."""
    try:
        # Get document count by type
        pdf_documents = await count_items_by_metadata(filter_key="type", filter_value="pdf")
        web_documents = await count_items_by_metadata(filter_key="type", filter_value="web")
        
        # Get category counts
        categories = await count_items_by_metadata(filter_key="category")
        if not isinstance(categories, dict):
            categories = {}
        
        # Get source counts
        sources = await count_items_by_metadata(filter_key="source")
        if not isinstance(sources, dict):
            sources = {}
        
        # Get knowledge base counts
        knowledge_bases = await count_items_by_metadata(filter_key="knowledge_base_id", count_unique=True)
        if not isinstance(knowledge_bases, dict):
            knowledge_bases = {"default-kb": 0}
        
        # Get page count for PDFs
        total_pages_data = await count_items_by_metadata(filter_key="page_number", count_unique=True)
        
        # Handle total_pages properly
        total_pages = 0
        if isinstance(total_pages_data, dict):
            total_pages = len(total_pages_data)
        elif isinstance(total_pages_data, int):
            total_pages = total_pages_data
        
        # Get total chunks
        total_chunks = pdf_documents + web_documents
        
        # Get total documents using count_total_documents() for consistency with debug view
        total_documents = await count_total_documents()
        
        # Get total entries by counting unique document IDs
        document_ids = await count_items_by_metadata(filter_key="document_id", count_unique=True)
        total_entries = len(document_ids) if isinstance(document_ids, dict) else 0
        
        logger.info(f"Stats calculation: total_documents={total_documents}, total_entries={total_entries}")
        
        return KnowledgeBaseStats(
            total_documents=total_documents,
            total_entries=total_entries,
            total_pages=total_pages,
            total_chunks=total_chunks,
            by_source=sources,
            by_category=categories,
            knowledge_bases=knowledge_bases,
            last_updated=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error getting knowledge base stats: {str(e)}")
        raise


async def reindex_kb() -> None:
    """Legacy function for reindexing knowledge base."""
    service = get_kb_service()
    return await service.reindex()


async def export_kb() -> Dict[str, Any]:
    """Legacy function for exporting knowledge base."""
    service = get_kb_service()
    return await service.export()


async def get_entry(entry_id: str) -> Dict[str, Any]:
    """Legacy function for getting a knowledge base entry by ID."""
    service = get_kb_service()
    return await service.get_entry(entry_id)


async def list_entries(
    limit: int = 10,
    offset: int = 0,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Legacy function for listing knowledge base entries."""
    service = get_kb_service()
    return await service.list_entries(limit, offset, filters)


async def delete_entry(entry_id: str) -> Dict[str, Any]:
    """Legacy function for deleting a knowledge base entry by ID."""
    service = get_kb_service()
    return await service.delete_entry(entry_id) 