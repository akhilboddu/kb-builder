import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import uuid
from datetime import datetime

# Import the application
from main import app
from app.models.knowledge_base import KnowledgeBaseCreate, DocumentMetadata

# Create a test client
client = TestClient(app)

# Mock user for testing
@pytest.fixture
def mock_user():
    """Create a mock user for testing"""
    from app.models.user import User, UserLimits
    
    limits = UserLimits(
        max_bots=3,
        max_documents_per_kb=10,
        max_kb_per_bot=5
    )
    
    return User(
        id="user-123",
        email="test@example.com",
        limits=limits
    )

@pytest.fixture
def mock_auth_dependency():
    """Override the auth dependency for testing"""
    with patch('app.core.dependencies.get_current_user') as mock:
        yield mock

@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing"""
    with patch('app.core.database.supabase_client') as mock:
        yield mock

def test_create_knowledge_base(mock_auth_dependency, mock_supabase, mock_user):
    """Test creating a knowledge base"""
    # Set up mock user
    mock_auth_dependency.return_value = mock_user
    
    # Set up mock for validate_bot_access
    with patch('app.routers.knowledge_base.validate_bot_access') as mock_validate:
        mock_validate.return_value = True
        
        # Set up mock for Supabase count query
        mock_count_response = MagicMock()
        mock_count_response.count = 2  # Below the limit of 5
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_count_response
        
        # Set up mock for Supabase insert
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()
        
        # Data for the test
        kb_data = {
            "name": "Test Knowledge Base",
            "bot_id": "bot-123"
        }
        
        # Make the request
        response = client.post("/api/knowledge-base/create", json=kb_data)
        
        # Assert response
        assert response.status_code == 200
        assert response.json()["name"] == "Test Knowledge Base"
        assert response.json()["bot_id"] == "bot-123"
        assert "id" in response.json()
        
        # Verify Supabase calls
        mock_supabase.table.assert_any_call("knowledge_bases")

def test_list_knowledge_bases(mock_auth_dependency, mock_supabase, mock_user):
    """Test listing knowledge bases for a bot"""
    # Set up mock user
    mock_auth_dependency.return_value = mock_user
    
    # Set up mock for validate_bot_access
    with patch('app.routers.knowledge_base.validate_bot_access') as mock_validate:
        mock_validate.return_value = True
        
        # Set up mock for Supabase query
        kb1_id = str(uuid.uuid4())
        kb2_id = str(uuid.uuid4())
        bot_id = "bot-123"
        mock_response = MagicMock()
        mock_response.data = [
            {
                "id": kb1_id,
                "bot_id": bot_id,
                "name": "KB 1",
                "created_at": datetime.now().isoformat()
            },
            {
                "id": kb2_id,
                "bot_id": bot_id,
                "name": "KB 2",
                "created_at": datetime.now().isoformat()
            }
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        # Make the request
        response = client.get(f"/api/knowledge-base/list/{bot_id}")
        
        # Assert response
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["name"] == "KB 1"
        assert response.json()[1]["name"] == "KB 2"

@patch('app.services.document_processor.process_pdf_file')
def test_upload_document(mock_process_pdf, mock_auth_dependency, mock_supabase, mock_user):
    """Test uploading a document"""
    # Set up mock user and dependencies
    mock_auth_dependency.return_value = mock_user
    
    # Mock the knowledge base query
    kb_id = str(uuid.uuid4())
    bot_id = "bot-123"
    kb_response = MagicMock()
    kb_response.data = [{"id": kb_id, "bot_id": bot_id}]
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        kb_response,  # knowledge base lookup
        MagicMock(count=5)  # document count (below limit)
    ]
    
    # Mock the PDF processing
    mock_process_pdf.return_value = (3, ["chunk1", "chunk2", "chunk3"])
    
    # Set up mock for validate_bot_access
    with patch('app.routers.knowledge_base.validate_bot_access') as mock_validate:
        mock_validate.return_value = True
        
        # Create mock file
        import io
        file_content = b"%PDF-1.5\nTest PDF content"
        mock_file = io.BytesIO(file_content)
        
        # Make the request with form data
        from starlette.testclient import TestClient
        client = TestClient(app)
        response = client.post(
            f"/api/knowledge-base/documents/upload",
            files={"file": ("test.pdf", mock_file, "application/pdf")},
            data={"knowledge_base_id": kb_id, "title": "Test Document"}
        )
        
        # Assert response
        assert response.status_code == 200
        assert response.json()["title"] == "Test Document"
        assert response.json()["knowledge_base_id"] == kb_id
        assert response.json()["status"] == "completed"
        
        # Verify the PDF processing was called
        mock_process_pdf.assert_called_once()