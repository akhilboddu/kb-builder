"""Test document service module."""
import pytest
from datetime import datetime
from fastapi import UploadFile
from io import BytesIO
from app.services.document_service import (
    process_pdf,
    get_document_info,
    get_documents_info,
    delete_document_info,
    get_document_chunks
)
from app.models.document import DocumentInfo
from app.db.document_repository import save_document
import uuid

class MockUploadFile(UploadFile):
    """Mock UploadFile for testing."""
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self._content = content
        self._file = BytesIO(content)
    
    async def read(self) -> bytes:
        return self._content

@pytest.mark.asyncio
async def test_process_pdf(db_session):
    """Test processing a PDF document."""
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
    result = await get_document_info(doc.document_id, db_session)
    
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
async def test_get_documents(db_session):
    """Test getting all documents."""
    # Create test documents
    docs = []
    for i in range(3):
        doc = DocumentInfo(
            document_id=str(uuid.uuid4()),
            title=f"Test Document {i}",
            filename=f"test{i}.pdf",
            category="Test",
            tags=["test"],
            page_count=1,
            chunk_count=i+1,
            created_at=datetime.now(),
            processing_status="completed"
        )
        await save_document(doc, db_session)
        docs.append(doc)
    
    # Get all documents
    result = await get_documents_info(db_session)
    
    # Verify documents
    assert len(result) == len(docs)
    for doc in docs:
        found = next((d for d in result if d.document_id == doc.document_id), None)
        assert found is not None
        assert found.title == doc.title
        assert found.filename == doc.filename
        assert found.category == doc.category
        assert found.tags == doc.tags
        assert found.page_count == doc.page_count
        assert found.chunk_count == doc.chunk_count
        assert found.processing_status == doc.processing_status

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
    result = await get_documents_info(
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
async def test_get_document(db_session):
    """Test getting a specific document."""
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
    result = await get_document_info(doc.document_id, db_session)
    
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
    await delete_document_info(doc.document_id, db_session)
    
    # Verify document is deleted
    result = await get_document_info(doc.document_id, db_session)
    assert result is None

@pytest.mark.asyncio
async def test_get_document_chunks(db_session):
    """Test getting document chunks."""
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
    
    # Get chunks
    result = await get_document_info(doc.document_id, db_session)
    
    # Verify chunks
    assert result is not None
    assert result.document_id == doc.document_id