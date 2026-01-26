from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "env" in data

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "Dental Bot API"

def test_chat_endpoint_mock_llm():
    """Test the chat endpoint with a mocked LLM response."""
    # Patch the chat_completion function where it is used in the chat route
    with patch("app.routes.chat.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = "Hello! This is a mocked response."
        
        payload = {
            "clinic_id": "lemon-main",  # Use a demo clinic ID to avoid DB lookups
            "message": "Hello",
            "session_id": "test-session-123"
        }
        
        response = client.post("/chat", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == "Hello! This is a mocked response."
        assert data["session_id"] == "test-session-123"
        assert not data["handoff"]
        
        # Verify the mock was called
        mock_chat.assert_called_once()