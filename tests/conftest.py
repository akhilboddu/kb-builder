"""
Test fixtures and configuration.
"""
import os
import pytest
import pytest_asyncio
import uuid
from datetime import datetime
from typing import List
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.main import app
from app.db.base import Base
from app.models.document import DocumentInfo
from app.db.session import get_db
from app.db.document_repository import save_document


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=True,
        future=True
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def db_session(db_engine):
    """Create a test database session."""
    async_session = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        yield session
        await session.rollback()
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client(db_session):
    """Create a test client."""
    app.dependency_overrides = {}
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides["get_db"] = override_get_db
    return TestClient(app)


@pytest_asyncio.fixture
async def sample_document_info(db_session):
    """Create sample documents for testing."""
    docs = []
    for i in range(4):
        doc = DocumentInfo(
            document_id=str(uuid.uuid4()),
            title=f"Test Document {i}",
            filename=f"test{i}.pdf",
            category="test",
            tags=["test", "even"] if i % 2 == 0 else ["test", "odd"],
            page_count=1,
            chunk_count=i + 1,
            created_at=datetime.now(),
            processing_status="completed"
        )
        await save_document(doc, db_session)
        docs.append(doc)
    return docs


@pytest.fixture
def sample_pdf():
    """Create a minimal valid PDF for testing."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R>>endobj\n"
        b"4 0 obj<</Length 51>>\n"
        b"stream\n"
        b"BT\n"
        b"/F1 12 Tf\n"
        b"100 700 Td\n"
        b"(Sample test content for PDF) Tj\n"
        b"ET\n"
        b"endstream\n"
        b"endobj\n"
        b"xref\n"
        b"0 5\n"
        b"0000000000 65535 f\n"
        b"0000000009 00000 n\n"
        b"0000000057 00000 n\n"
        b"0000000110 00000 n\n"
        b"0000000183 00000 n\n"
        b"trailer<</Size 5/Root 1 0 R>>\n"
        b"startxref\n"
        b"300\n"
        b"%%EOF"
    )


def create_test_file(filename: str, content: bytes) -> dict:
    """Create a test file for upload."""
    return {"file": (filename, content, "application/pdf")} 