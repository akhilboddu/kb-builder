"""
Vector store integration with ChromaDB.
"""
import logging
from typing import List, Dict, Any, Optional, Union
import os
import asyncio
import chromadb
from chromadb.config import Settings
from chromadb.errors import InvalidCollectionException
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global variables for singleton pattern
_client = None
_collection = None
_embedding_model = None

async def get_embedding_model() -> SentenceTransformer:
    """
    Get the embedding model as a singleton.
    
    Returns:
        SentenceTransformer model
    """
    global _embedding_model
    
    if _embedding_model is None:
        try:
            # Load the model
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise ValueError(f"Failed to load embedding model: {str(e)}")
        
    return _embedding_model

async def get_vector_store():
    """
    Get ChromaDB client and collection as singletons.
    
    Returns:
        Tuple of (client, collection)
    """
    global _client, _collection
    
    if _client is None:
        try:
            # Create the client
            logger.info(f"Initializing ChromaDB at {settings.CHROMA_PERSIST_DIRECTORY}")
            _client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY,
                settings=Settings(
                    allow_reset=True,
                    anonymized_telemetry=False
                )
            )
            
            # Get or create the collection
            try:
                try:
                    _collection = _client.get_collection("knowledge_base")
                    logger.info("Retrieved existing ChromaDB collection")
                except InvalidCollectionException:
                    logger.info("Creating new ChromaDB collection")
                    _collection = _client.create_collection(
                        name="knowledge_base",
                        metadata={"hnsw:space": "cosine"}
                    )
                
                # Test if collection has proper embedding dimension
                model = await get_embedding_model()
                test_embedding = model.encode(["Test embedding dimension"]).tolist()
                embedding_dim = len(test_embedding[0])
                
                # Add a test item to verify dimensions match
                try:
                    test_id = "test_dimension_" + str(os.urandom(4).hex())
                    _collection.add(
                        ids=[test_id],
                        embeddings=test_embedding,
                        documents=["Test document"],
                        metadatas=[{"test": "true"}]
                    )
                    # If successful, delete the test item
                    _collection.delete(ids=[test_id])
                except Exception as e:
                    if "dimension" in str(e).lower():
                        logger.warning(f"Embedding dimension mismatch. Recreating collection. Error: {str(e)}")
                        # Delete and recreate collection
                        _client.delete_collection("knowledge_base")
                        _collection = _client.create_collection(
                            name="knowledge_base",
                            metadata={"hnsw:space": "cosine"}
                        )
                    else:
                        raise
                        
            except Exception as e:
                if "dimension" not in str(e).lower():
                    logger.error(f"Error initializing collection: {str(e)}")
                    raise
                
                logger.warning(f"Error with collection dimensions: {str(e)}")
                # Delete and recreate collection
                try:
                    _client.delete_collection("knowledge_base")
                except:
                    pass
                    
                _collection = _client.create_collection(
                    name="knowledge_base",
                    metadata={"hnsw:space": "cosine"}
                )
                
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")
            raise ValueError(f"Failed to initialize vector store: {str(e)}")
    
    return _client, _collection

async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts.
    
    Args:
        texts: List of text strings
        
    Returns:
        List of embedding vectors
    """
    try:
        model = await get_embedding_model()
        
        # Generate embeddings
        embeddings = model.encode(texts, show_progress_bar=False)
        
        return embeddings.tolist()
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {str(e)}")
        raise ValueError(f"Failed to generate embeddings: {str(e)}")

def _convert_metadata_value(value: Any) -> str:
    """
    Convert metadata value to string.
    
    This function ensures all metadata values are properly converted to strings
    for consistent storage and retrieval with ChromaDB.
    """
    if value is None:
        return ""
    elif isinstance(value, (bool, int, float)):
        return str(value)
    elif isinstance(value, list):
        return ",".join(str(v) for v in value)
    else:
        # Force to string to ensure consistent handling
        return str(value)

def _prepare_metadata(metadata: Dict[str, Any]) -> Dict[str, str]:
    """Prepare metadata for ChromaDB by converting values to strings."""
    result = {k: _convert_metadata_value(v) for k, v in metadata.items()}
    logger.debug(f"Prepared metadata: Original: {metadata}, Converted: {result}")
    return result

async def add_chunks_to_vector_store(chunks_with_metadata: List[Dict[str, Any]]) -> None:
    """Add document chunks to vector store."""
    if not chunks_with_metadata:
        logger.warning("No chunks to add to vector store")
        return

    try:
        # Extract texts and metadata
        texts = [chunk["content"] for chunk in chunks_with_metadata]
        metadata = [_prepare_metadata(chunk["metadata"]) for chunk in chunks_with_metadata]
        
        # Log sample metadata for debugging
        if metadata and len(metadata) > 0:
            logger.info(f"Sample metadata being added to vector store: {metadata[0]}")
            if "knowledge_base_id" in metadata[0]:
                logger.info(f"Knowledge base ID in sample: '{metadata[0]['knowledge_base_id']}'")
                # Ensure it's properly converted to string
                metadata[0]["knowledge_base_id"] = str(metadata[0]["knowledge_base_id"])
                logger.info(f"Converted knowledge_base_id to string: '{metadata[0]['knowledge_base_id']}'")
        
        # Ensure all knowledge_base_id values are properly converted to strings
        for meta in metadata:
            if "knowledge_base_id" in meta:
                meta["knowledge_base_id"] = str(meta["knowledge_base_id"])
        
        # Generate unique IDs for each chunk
        ids = []
        for i, chunk in enumerate(chunks_with_metadata):
            chunk_metadata = chunk.get("metadata", {})
            doc_id = chunk_metadata.get("document_id", f"doc-{i}")
            chunk_id = f"{doc_id}_{i}"
            ids.append(chunk_id)

        # Generate embeddings
        embeddings = await generate_embeddings(texts)

        # Add to collection
        _, collection = await get_vector_store()
        collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadata,
            ids=ids
        )

        logger.info(f"Added {len(chunks_with_metadata)} chunks to vector store")
    except Exception as e:
        logger.error(f"Failed to add chunks to vector store: {str(e)}")
        raise ValueError(f"Failed to add chunks to vector store: {str(e)}")

async def search_vector_store(
    query: str,
    filter_conditions: Optional[Dict[str, Any]] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search vector store for relevant chunks.
    
    Args:
        query: Search query text
        filter_conditions: Optional metadata filters
        limit: Maximum number of results to return
        
    Returns:
        List of dictionaries with document, metadata, and score
    """
    try:
        # Generate query embedding
        query_embedding = await generate_embeddings([query])
        
        # Prepare filter conditions
        where_clause = None
        if filter_conditions:
            # Ensure all filter values are properly converted to strings
            where_clause = {}
            for k, v in filter_conditions.items():
                if v is not None:
                    where_clause[k] = _convert_metadata_value(v)
            
            logger.info(f"Search filter conditions - Original: {filter_conditions}, Converted: {where_clause}")
            
            # Special handling for empty where_clause
            if not where_clause:
                where_clause = None
                logger.info("No valid filter conditions after conversion")
        else:
            logger.info("No filter conditions provided for search")

        # Search collection
        _, collection = await get_vector_store()
        try:
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=limit,
                where=where_clause
            )
            
            logger.info(f"ChromaDB query results count: {len(results.get('ids', []))}")
            
            # If we have knowledge_base_id in the filter and got no results, log more info
            if where_clause and "knowledge_base_id" in where_clause and not results.get('ids'):
                # Get a sample of metadata to see what knowledge_base_id values exist
                sample_results = collection.get(limit=5)
                if sample_results and sample_results.get('metadatas'):
                    kb_ids = set()
                    for metadata in sample_results['metadatas']:
                        if metadata and "knowledge_base_id" in metadata:
                            kb_ids.add(metadata["knowledge_base_id"])
                    logger.info(f"Sample knowledge_base_id values in DB: {kb_ids}")
        except Exception as e:
            logger.error(f"ChromaDB query failed: {str(e)}")
            # Return an empty result list
            return []
        
        # Defensive check for results
        if not results or not isinstance(results, dict):
            logger.warning("ChromaDB returned invalid results format")
            return []
            
        # Debug logging
        logger.info(f"ChromaDB query results keys: {list(results.keys())}")
        
        # Format results - simpler and more defensive approach
        formatted_results = []
        
        # Check for required keys
        if "ids" not in results or not results["ids"]:
            logger.warning("No ids in ChromaDB results")
            return []
            
        # Process each result
        for i in range(len(results["ids"])):
            # Skip if the ID is None
            if results["ids"][i] is None:
                continue
                
            # Get document content safely
            document = ""
            if "documents" in results and i < len(results.get("documents", [])):
                doc_value = results["documents"][i]
                if doc_value is not None:
                    if isinstance(doc_value, list):
                        if doc_value and doc_value[0] is not None:
                            document = str(doc_value[0])
                    else:
                        document = str(doc_value)
            
            # Get metadata safely
            metadata = {}
            if "metadatas" in results and i < len(results.get("metadatas", [])):
                meta_value = results["metadatas"][i]
                if meta_value is not None and isinstance(meta_value, dict):
                    metadata = meta_value
            
            # Get score safely
            score = 0.0
            if "distances" in results and i < len(results.get("distances", [])):
                dist_value = results["distances"][i]
                if dist_value is not None:
                    try:
                        if isinstance(dist_value, list):
                            if dist_value and dist_value[0] is not None:
                                score = float(dist_value[0])
                        else:
                            score = float(dist_value)
                    except (ValueError, TypeError):
                        logger.warning(f"Could not convert distance to float: {dist_value}")
            
            # Create the result object
            formatted_results.append({
                "id": str(results["ids"][i]),
                "document": document,
                "metadata": metadata,
                "score": score
            })
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"Failed to search vector store: {str(e)}")
        raise ValueError(f"Failed to search vector store: {str(e)}")

async def get_chunks_by_document_id(document_id: str) -> List[Dict[str, Any]]:
    """Get all chunks for a specific document."""
    try:
        _, collection = await get_vector_store()
        results = collection.get(
            where={"document_id": document_id}
        )
        
        # Format results
        chunks = []
        for i, text in enumerate(results["documents"]):
            chunk = {
                "content": text,
                "metadata": results["metadatas"][i]
            }
            chunks.append(chunk)
        
        return chunks
    except Exception as e:
        logger.error(f"Failed to get chunks from vector store: {str(e)}")
        raise ValueError(f"Failed to get chunks from vector store: {str(e)}")

async def count_items_by_metadata(
    filter_key: str,
    filter_value: Optional[Any] = None,
    count_unique: bool = False
) -> Union[int, Dict[str, int]]:
    """
    Count items by metadata field.
    
    Args:
        filter_key: Metadata key to count
        filter_value: Optional specific value to count
        count_unique: Whether to count unique values
        
    Returns:
        Count or dictionary of counts by value
    """
    try:
        _, collection = await get_vector_store()
        
        # Prepare where clause
        where_clause = None
        if filter_value is not None:
            # Convert the value properly
            str_value = _convert_metadata_value(filter_value)
            where_clause = {filter_key: str_value}
            logger.info(f"Counting with filter: {filter_key}={filter_value} (converted: {str_value})")
        
        # Get all items with the specified metadata field
        results = collection.get(
            where=where_clause
        )
        
        if not results["documents"]:
            logger.info(f"No results found for filter_key={filter_key}, filter_value={filter_value}")
            return 0 if not count_unique else {}
        
        # We'll always build a dictionary of counts by value
        unique_values = {}
        for metadata in results["metadatas"]:
            value = metadata.get(filter_key, "")
            unique_values[value] = unique_values.get(value, 0) + 1
        
        # Log the results
        if count_unique:
            logger.info(f"Found {len(unique_values)} unique values for {filter_key}")
            if len(unique_values) < 10:  # Only log if small number of values
                logger.info(f"Unique values: {unique_values}")
        
        # Return the count dictionary if requested, or the specific count if a filter value was provided
        if count_unique or not filter_value:
            return unique_values
        else:
            # Return total count for a specific filter value
            return len(results["documents"])
            
    except Exception as e:
        logger.error(f"Failed to count items by metadata: {str(e)}")
        raise ValueError(f"Failed to count items by metadata: {str(e)}")

async def get_documents_by_metadata(field: str, value: str) -> List[Dict[str, Any]]:
    """
    Retrieve documents from the vector store by metadata field.
    
    Args:
        field: Metadata field to filter by (e.g., 'document_id')
        value: Value to match
        
    Returns:
        List of dictionaries with document data
    """
    try:
        # Convert value to string according to our metadata convention
        str_value = _convert_metadata_value(value)
        
        # Get the collection
        _, collection = await get_vector_store()
        
        # Query the collection
        results = collection.get(
            where={field: str_value}
        )
        
        if not results or not results.get("documents"):
            logger.warning(f"No documents found with {field}={value}")
            return []
            
        # Format results
        formatted_results = []
        for i in range(len(results["ids"])):
            # Skip if no document
            if i >= len(results.get("documents", [])) or results["documents"][i] is None:
                continue
                
            # Get metadata safely
            metadata = {}
            if "metadatas" in results and i < len(results.get("metadatas", [])):
                meta_value = results["metadatas"][i]
                if meta_value is not None and isinstance(meta_value, dict):
                    metadata = meta_value
            
            # Create the result object
            formatted_results.append({
                "id": str(results["ids"][i]),
                "document": results["documents"][i],
                "metadata": metadata
            })
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"Failed to get documents by metadata: {str(e)}")
        raise ValueError(f"Failed to get documents by metadata: {str(e)}")

async def count_total_documents() -> int:
    """
    Count the total number of documents in the vector store.
    
    Returns:
        Total document count
    """
    try:
        # Get the collection
        _, collection = await get_vector_store()
        
        # Get total chunks count using a direct API call
        try:
            collection_info = collection._collection.count()
            logger.info(f"Total chunks in collection: {collection_info}")
            
            # If we have chunks, find how many unique documents they belong to
            if collection_info > 0:
                # Get a small batch of documents to check if they have document_id
                sample = collection.get(limit=1)
                if sample and sample.get("metadatas") and "document_id" in sample["metadatas"][0]:
                    logger.info("Documents have document_id metadata, counting unique documents")
                    # For consistency with the rest of the app, return the total count
                    return collection_info
            
            return collection_info
            
        except Exception as inner_e:
            logger.warning(f"Error using direct count, using fallback: {inner_e}")
            # Fallback: use get with a limit of 1 just to check if collection has data
            results = collection.get(limit=1)
            has_documents = len(results.get("ids", [])) > 0
            logger.info(f"Collection has documents: {has_documents}")
            return 1 if has_documents else 0
            
    except Exception as e:
        logger.error(f"Failed to count documents: {str(e)}")
        return 0

async def get_all_documents(limit: int = 100, offset: int = 0, filter_conditions: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Retrieve all documents from the vector store with pagination.
    
    Args:
        limit: Maximum number of documents to return
        offset: Number of documents to skip (for pagination)
        filter_conditions: Optional metadata filters
        
    Returns:
        List of dictionaries with document data
    """
    try:
        # Get the collection
        _, collection = await get_vector_store()
        
        # First, check total document count
        total_count = await count_total_documents()
        logger.info(f"Total documents in collection before query: {total_count}")
        
        # Prepare filter conditions
        where_clause = None
        if filter_conditions:
            # Ensure all filter values are properly converted to strings
            where_clause = {}
            for k, v in filter_conditions.items():
                if v is not None:
                    where_clause[k] = _convert_metadata_value(v)
            
            # Special handling for knowledge_base_id to ensure exact matching
            if "knowledge_base_id" in where_clause:
                kb_id = where_clause["knowledge_base_id"]
                logger.info(f"Applying knowledge_base_id filter with value: '{kb_id}'")
                # Ensure it's a string
                where_clause["knowledge_base_id"] = str(kb_id)
                # Log some diagnostic info
                try:
                    # Get a small sample of documents to see knowledge_base_id values
                    sample = collection.get(limit=5)
                    if sample and sample.get("metadatas"):
                        kb_ids_in_db = set()
                        for metadata in sample.get("metadatas", []):
                            if metadata and "knowledge_base_id" in metadata:
                                kb_ids_in_db.add(metadata["knowledge_base_id"])
                        logger.info(f"Sample knowledge_base_id values in DB: {kb_ids_in_db}")
                except Exception as e:
                    logger.warning(f"Couldn't retrieve sample knowledge_base_id values: {e}")
            
            logger.info(f"Get documents filter conditions - Original: {filter_conditions}, Converted: {where_clause}")
            
            # Special handling for empty where_clause
            if not where_clause:
                where_clause = None
                logger.info("No valid filter conditions after conversion")
        else:
            logger.info("No filter conditions provided for get_all_documents")
        
        # Get all documents matching the filter
        logger.info(f"Fetching documents with limit={limit}, offset={offset}, filters={where_clause}")
        
        # Use the requested limit (don't override with 10000)
        actual_limit = limit
        
        # Query the collection
        try:
            results = collection.get(
                where=where_clause,
                limit=actual_limit,
                offset=offset
            )
            
            logger.info(f"Got {len(results.get('ids', []))} results from ChromaDB")
            
            # If we have knowledge_base_id in the filter and got no results, log more info
            if where_clause and "knowledge_base_id" in where_clause and not results.get('ids'):
                # Get a sample of metadata to see what knowledge_base_id values exist
                sample_results = collection.get(limit=5)
                if sample_results and sample_results.get('metadatas'):
                    kb_ids = set()
                    for metadata in sample_results['metadatas']:
                        if metadata and "knowledge_base_id" in metadata:
                            kb_ids.add(metadata["knowledge_base_id"])
                    logger.info(f"Sample knowledge_base_id values in DB: {kb_ids}")
                    
                    # Try fetching with different quotation/formatting to debug issues
                    kb_id = where_clause["knowledge_base_id"]
                    alternative_formats = [
                        kb_id.strip(),
                        f'"{kb_id}"',
                        kb_id.lower(),
                        kb_id.upper()
                    ]
                    
                    for alt_format in alternative_formats:
                        if alt_format == kb_id:
                            continue
                        logger.info(f"Trying alternative format for knowledge_base_id: '{alt_format}'")
                        try:
                            alt_results = collection.get(
                                where={"knowledge_base_id": alt_format},
                                limit=5
                            )
                            if alt_results and alt_results.get('ids'):
                                logger.info(f"Found {len(alt_results.get('ids'))} results with alt format '{alt_format}'")
                        except Exception as e:
                            logger.warning(f"Error with alt format '{alt_format}': {e}")
        except Exception as e:
            logger.error(f"ChromaDB get operation failed: {str(e)}")
            return []
        
        if not results or not results.get("documents"):
            logger.warning(f"No documents found (limit={limit}, offset={offset})")
            return []
            
        # Format results
        formatted_results = []
        for i in range(len(results["ids"])):
            # Skip if no document
            if i >= len(results.get("documents", [])) or results["documents"][i] is None:
                continue
                
            # Get metadata safely
            metadata = {}
            if "metadatas" in results and i < len(results.get("metadatas", [])):
                meta_value = results["metadatas"][i]
                if meta_value is not None and isinstance(meta_value, dict):
                    metadata = meta_value
            
            # Create the result object
            formatted_results.append({
                "id": str(results["ids"][i]),
                "document": results["documents"][i],
                "metadata": metadata
            })
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"Failed to get all documents: {str(e)}")
        raise ValueError(f"Failed to get all documents: {str(e)}")

__all__ = [
    'add_chunks_to_vector_store',
    'search_vector_store',
    'get_chunks_by_document_id',
    'count_items_by_metadata',
    'get_documents_by_metadata',
    'get_all_documents',
    'count_total_documents'
]