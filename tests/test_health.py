import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import the application
from main import app

# Create a test client
client = TestClient(app)

@patch('app.routers.health.supabase_client')
@patch('app.routers.health.openai.models')
def test_health_endpoint_healthy(mock_openai_models, mock_supabase_client):
    """Test the health endpoint when all services are healthy"""
    # Mock Supabase response
    mock_supabase_client.rpc.return_value.execute.return_value = {"version": "PostgreSQL 14.5"}
    
    # Mock OpenAI response
    mock_openai_models.list.return_value = ["gpt-4", "text-embedding-3-large"]
    
    # Make the request
    response = client.get("/health")
    
    # Assert response
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["services"]["supabase"]["status"] == "healthy"
    assert response.json()["services"]["openai"]["status"] == "healthy"

@patch('app.routers.health.supabase_client')
@patch('app.routers.health.openai.models')
def test_health_endpoint_degraded(mock_openai_models, mock_supabase_client):
    """Test the health endpoint when a service is unhealthy"""
    # Mock Supabase error
    mock_supabase_client.rpc.return_value.execute.side_effect = Exception("Database connection error")
    
    # Mock OpenAI response
    mock_openai_models.list.return_value = ["gpt-4", "text-embedding-3-large"]
    
    # Make the request - should return 503
    with pytest.raises(Exception) as exc_info:
        response = client.get("/health")
        
    # Assert response contains error details
    assert "503" in str(exc_info.value)  # HTTP 503 Service Unavailable