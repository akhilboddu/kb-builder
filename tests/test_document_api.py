"""
Tests for document API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from tests.conftest import create_test_file


def test_upload_pdf(client: TestClient, sample_pdf: bytes):
    """Test uploading a PDF document."""
    # Create test file
    files = create_test_file("test.pdf", sample_pdf)
    
    # Add form data
    data = {
        "title": "Test Document",
        "category": "Test",
        "tags": "test,sample"
    }
    
    # Upload file
    response = client.post(
        "/api/documents/upload-pdf",
        files=files,
        data=data
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data
    assert data["status"] == "success"
    assert data["message"] == "Document processed successfully"


def test_upload_invalid_file(client: TestClient):
    """Test uploading a non-PDF file."""
    # Create invalid file
    files = create_test_file("test.txt", b"Not a PDF")
    
    # Add required form data
    data = {
        "title": "Test Document"
    }
    
    # Upload file
    response = client.post(
        "/api/documents/upload-pdf",
        files=files,
        data=data
    )
    
    # Verify response
    assert response.status_code == 400
    assert response.json()["detail"] == "File must be a PDF"


def test_list_documents(client: TestClient, sample_pdf: bytes):
    """Test listing documents with filters."""
    # Upload test documents
    doc_ids = []
    categories = ["Category A", "Category A", "Category B"]
    
    for i, category in enumerate(categories):
        files = create_test_file(f"test{i}.pdf", sample_pdf)
        data = {
            "title": f"Test Document {i}",
            "category": category,
            "tags": f"test,group{i}"
        }
        response = client.post("/api/documents/upload-pdf", files=files, data=data)
        assert response.status_code == 200
        doc_ids.append(response.json()["document_id"])
    
    # Test listing all documents
    response = client.get("/api/documents")
    assert response.status_code == 200
    documents = response.json()
    assert len(documents) == 3
    
    # Test filtering by category
    response = client.get("/api/documents?category=Category A")
    assert response.status_code == 200
    documents = response.json()
    assert len(documents) == 2
    
    # Test filtering by tags
    response = client.get("/api/documents?tags=test,group0")
    assert response.status_code == 200
    documents = response.json()
    assert len(documents) == 1


def test_get_document(client: TestClient, sample_pdf: bytes):
    """Test getting a specific document."""
    # Upload test document
    files = create_test_file("test.pdf", sample_pdf)
    data = {
        "title": "Test Document",
        "category": "Test",
        "tags": "test,sample"
    }
    response = client.post("/api/documents/upload-pdf", files=files, data=data)
    assert response.status_code == 200
    doc_id = response.json()["document_id"]
    
    # Get document
    response = client.get(f"/api/documents/{doc_id}")
    assert response.status_code == 200
    document = response.json()
    assert document["document_id"] == doc_id
    assert document["title"] == "Test Document"
    assert document["category"] == "Test"
    assert document["tags"] == ["test", "sample"]
    
    # Test getting non-existent document
    response = client.get("/api/documents/non-existent-id")
    assert response.status_code == 404


def test_delete_document(client: TestClient, sample_pdf: bytes):
    """Test deleting a document."""
    # Upload test document
    files = create_test_file("test.pdf", sample_pdf)
    data = {
        "title": "Test Document",
        "category": "Test",
        "tags": "test,sample"
    }
    response = client.post("/api/documents/upload-pdf", files=files, data=data)
    assert response.status_code == 200
    doc_id = response.json()["document_id"]
    
    # Delete document
    response = client.delete(f"/api/documents/{doc_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == doc_id
    assert data["status"] == "success"
    assert data["message"] == "Document deleted successfully"
    
    # Verify document is deleted
    response = client.get(f"/api/documents/{doc_id}")
    assert response.status_code == 404
    
    # Test deleting non-existent document
    response = client.delete("/api/documents/non-existent-id")
    assert response.status_code == 404 