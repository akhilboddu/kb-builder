"""
Tests for document repository functionality.
"""
import pytest
import uuid
from datetime import datetime

from app.models.document import DocumentInfo
from app.db.document_repository import (
    save_document,
    get_document,
    get_documents,
    update_document,
    delete_document
)


@pytest.mark.asyncio
async def test_save_and_get_document(db_session):
    """Test saving and getting a document."""
    # Create test document
    doc = DocumentInfo(
        document_id=str(uuid.uuid4()),
        title="Test Document",
        filename="test.pdf",
        category="Test",
        tags=["test"],
        page_count=1,
        chunk_count=0,
        created_at=datetime.now(),
        processing_status="processing"
    )
    
    # Save document
    await save_document(doc, db_session)
    
    # Get document
    result = await get_document(doc.document_id, db_session)
    
    # Verify document
    assert result is not None
    assert result.document_id == doc.document_id
    assert result.title == doc.title
    assert result.filename == doc.filename
    assert result.category == doc.category
    assert result.tags == doc.tags
    assert result.page_count == doc.page_count
    assert result.chunk_count == doc.chunk_count
    assert result.processing_status == doc.processing_status


@pytest.mark.asyncio
async def test_update_document(db_session):
    """Test updating a document."""
    # Create test document
    doc = DocumentInfo(
        document_id=str(uuid.uuid4()),
        title="Test Document",
        filename="test.pdf",
        category="Test",
        tags=["test"],
        page_count=1,
        chunk_count=0,
        created_at=datetime.now(),
        processing_status="processing"
    )
    
    # Save document
    await save_document(doc, db_session)
    
    # Update document
    doc.title = "Updated Title"
    doc.tags = ["test", "updated"]
    await update_document(doc, db_session)
    
    # Get updated document
    result = await get_document(doc.document_id, db_session)
    
    # Verify document
    assert result is not None
    assert result.title == "Updated Title"
    assert result.tags == ["test", "updated"]


@pytest.mark.asyncio
async def test_get_documents_with_filters(db_session):
    """Test getting documents with filters."""
    # Create test documents
    docs = []
    for i in range(4):
        doc = DocumentInfo(
            document_id=str(uuid.uuid4()),
            title=f"Test Document {i}",
            filename=f"test{i}.pdf",
            category="test",
            tags=["test", "even" if i % 2 == 0 else "odd"],
            page_count=1,
            chunk_count=i+1,
            created_at=datetime.now(),
            processing_status="completed"
        )
        await save_document(doc, db_session)
        docs.append(doc)
    
    # Get documents by category
    result = await get_documents(
        session=db_session,
        category="test",
        tags=["even"]
    )
    
    # Verify filtered documents
    assert len(result) == 2
    for doc in result:
        assert doc.category == "test"
        assert "even" in doc.tags


@pytest.mark.asyncio
async def test_delete_document(db_session):
    """Test deleting a document."""
    # Create test document
    doc = DocumentInfo(
        document_id=str(uuid.uuid4()),
        title="Test Document",
        filename="test.pdf",
        category="Test",
        tags=["test"],
        page_count=1,
        chunk_count=0,
        created_at=datetime.now(),
        processing_status="processing"
    )
    
    # Save document
    await save_document(doc, db_session)
    
    # Delete document
    await delete_document(doc.document_id, db_session)
    
    # Verify document is deleted
    result = await get_document(doc.document_id, db_session)
    assert result is None 