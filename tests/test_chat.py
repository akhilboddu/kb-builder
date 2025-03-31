import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import uuid
from datetime import datetime

# Import the application
from main import app
from app.models.chat import ConversationStatus, SenderType, ConfidenceScore

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

def test_create_conversation(mock_auth_dependency, mock_supabase, mock_user):
    """Test creating a conversation"""
    # Set up mock user
    mock_auth_dependency.return_value = mock_user
    
    # Set up mock for validate_bot_access
    with patch('app.routers.chat.validate_bot_access') as mock_validate:
        mock_validate.return_value = True
        
        # Set up mock for Supabase insert
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()
        
        # Data for the test
        conversation_data = {
            "bot_id": "bot-123"
        }
        
        # Make the request
        response = client.post("/api/chat/conversations", json=conversation_data)
        
        # Assert response
        assert response.status_code == 200
        assert response.json()["bot_id"] == "bot-123"
        assert response.json()["status"] == "open"
        assert "id" in response.json()
        
        # Verify Supabase calls
        mock_supabase.table.assert_any_call("conversations")

def test_list_conversations(mock_auth_dependency, mock_supabase, mock_user):
    """Test listing conversations for a bot"""
    # Set up mock user
    mock_auth_dependency.return_value = mock_user
    
    # Set up mock for validate_bot_access
    with patch('app.routers.chat.validate_bot_access') as mock_validate:
        mock_validate.return_value = True
        
        # Set up mock for Supabase query
        conv1_id = str(uuid.uuid4())
        conv2_id = str(uuid.uuid4())
        bot_id = "bot-123"
        mock_response = MagicMock()
        
        now = datetime.now().isoformat()
        mock_response.data = [
            {
                "id": conv1_id,
                "bot_id": bot_id,
                "status": "open",
                "created_at": now,
                "updated_at": now
            },
            {
                "id": conv2_id,
                "bot_id": bot_id,
                "status": "assigned",
                "created_at": now,
                "updated_at": now,
                "assigned_agent_id": "agent-123"
            }
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        # Make the request
        response = client.get(f"/api/chat/conversations/{bot_id}")
        
        # Assert response
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["status"] == "open"
        assert response.json()[1]["status"] == "assigned"
        assert response.json()[1]["assigned_agent_id"] == "agent-123"

@patch('app.services.realtime_service.save_message')
def test_create_message(mock_save_message, mock_auth_dependency, mock_supabase, mock_user):
    """Test creating a message"""
    # Set up mock user
    mock_auth_dependency.return_value = mock_user
    
    # Set up mock for validate_bot_access
    with patch('app.routers.chat.validate_bot_access') as mock_validate:
        mock_validate.return_value = True
        
        # Mock conversation response
        conv_id = str(uuid.uuid4())
        bot_id = "bot-123"
        mock_conv_response = MagicMock()
        mock_conv_response.data = [{
            "id": conv_id,
            "bot_id": bot_id,
            "status": "open",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_conv_response
        
        # Mock save_message response
        message_id = str(uuid.uuid4())
        now = datetime.now()
        mock_save_message.return_value = MagicMock(
            id=message_id,
            conversation_id=conv_id,
            sender_type=SenderType.USER,
            content="Hello bot",
            timestamp=now
        )
        
        # Message data
        message_data = {
            "conversation_id": conv_id,
            "sender_type": "user",
            "content": "Hello bot"
        }
        
        # Make the request
        response = client.post("/api/chat/messages", json=message_data)
        
        # Assert response
        assert response.status_code == 200
        assert response.json()["content"] == "Hello bot"
        assert response.json()["sender_type"] == "user"
        
        # Verify save_message was called
        mock_save_message.assert_called_once()

@patch('app.services.rag_service.query_bot')
@patch('app.services.realtime_service.save_message')
def test_query_conversation(mock_save_message, mock_query_bot, mock_auth_dependency, mock_supabase, mock_user):
    """Test querying a conversation"""
    # Set up mock user
    mock_auth_dependency.return_value = mock_user
    
    # Set up mock for validate_bot_access
    with patch('app.routers.chat.validate_bot_access') as mock_validate:
        mock_validate.return_value = True
        
        # Mock conversation response
        conv_id = str(uuid.uuid4())
        bot_id = "bot-123"
        mock_conv_response = MagicMock()
        mock_conv_response.data = [{
            "id": conv_id,
            "bot_id": bot_id,
            "status": "open",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_conv_response
        
        # Mock save_message responses for user and bot messages
        user_message_id = str(uuid.uuid4())
        bot_message_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Mock side effects to return different values on consecutive calls
        mock_save_message.side_effect = [
            MagicMock(
                id=user_message_id,
                conversation_id=conv_id,
                sender_type=SenderType.USER,
                content="What products do you offer?",
                timestamp=now
            ),
            MagicMock(
                id=bot_message_id,
                conversation_id=conv_id,
                sender_type=SenderType.BOT,
                content="We offer a range of software products for businesses.",
                timestamp=now,
                citations=[{"text": "Product catalog", "title": "Products"}],
                confidence_score=ConfidenceScore(
                    vector_similarity=0.85,
                    llm_self_assessment=0.9,
                    final_score=0.875
                )
            )
        ]
        
        # Mock query_bot response
        confidence = ConfidenceScore(
            vector_similarity=0.85,
            llm_self_assessment=0.9,
            final_score=0.875
        )
        mock_query_bot.return_value = (
            "We offer a range of software products for businesses.", 
            [{"text": "Product catalog", "title": "Products"}], 
            confidence,
            False  # doesn't need handover
        )
        
        # Make the request
        response = client.post(
            f"/api/chat/query?conversation_id={conv_id}&query=What products do you offer?"
        )
        
        # Assert response
        assert response.status_code == 200
        assert response.json()["sender_type"] == "bot"
        assert "We offer a range of software products" in response.json()["content"]
        assert response.json()["confidence_score"]["final_score"] == 0.875
        
        # Verify save_message was called twice (user message and bot response)
        assert mock_save_message.call_count == 2
        
        # Verify query_bot was called with correct args
        mock_query_bot.assert_called_once_with(
            conversation_id=conv_id,
            query="What products do you offer?"
        )