from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

from app.routes.chat import DEMO_CLINICS # To get clinic details for expected reply
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
    # Patch the chat_completion function and insert_message
    with patch("app.routes.chat.chat_completion", new_callable=AsyncMock) as mock_chat, \
         patch("app.supabase_db.insert_message", new_callable=AsyncMock) as mock_insert_message:
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
        # insert_message should be called twice (user and assistant)
        assert mock_insert_message.call_count == 2

def test_chat_endpoint_medical_emergency_guardrail():
    """Test that the medical emergency guardrail triggers correctly."""
    clinic_id = "smile-city-001"
    clinic_data = DEMO_CLINICS[clinic_id]
    
    expected_reply = (
        f"{clinic_data.get('emergency_instructions')}\n\n"
        f"If you cannot reach the clinic quickly, seek urgent medical care.\n\n"
        f"This assistant provides general information and does not replace professional medical advice."
    )

    with patch("app.services.guardrails.is_emergency", return_value=True), \
         patch("app.services.guardrails.is_symptom_or_diagnosis_request", return_value=False), \
         patch("app.supabase_db.insert_message", new_callable=AsyncMock) as mock_insert_message, \
         patch("app.routes.chat.chat_completion", new_callable=AsyncMock) as mock_chat_completion: # Ensure LLM is not called
        
        payload = {
            "clinic_id": clinic_id,
            "message": "I'm having a medical emergency!",
            "session_id": "test-emergency-session"
        }
        
        response = client.post("/chat", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["reply"] == expected_reply
        assert data["session_id"] == "test-emergency-session"
        assert data["handoff"] is True
        assert data["handoff_reason"] == "emergency"
        
        # Verify LLM was NOT called
        mock_chat_completion.assert_not_called()
        # Verify insert_message was called for the assistant's reply
        mock_insert_message.assert_called_once_with("test-emergency-session", "assistant", expected_reply)

def test_chat_endpoint_medical_symptom_guardrail():
    """Test that the medical symptom/diagnosis guardrail triggers correctly."""
    clinic_id = "smile-city-001"
    clinic_data = DEMO_CLINICS[clinic_id]
    
    expected_reply = (
        f"I can't provide medical advice or diagnose symptoms. "
        f"The safest step is to book an appointment so a clinician can assess you.\n\n"
        f"You can book here: {clinic_data.get('booking_url')}\n"
        f"Or contact the clinic: {clinic_data.get('contact_phone')} / {clinic_data.get('contact_email')}\n\n"
        f"This assistant provides general information and does not replace professional medical advice."
    )

    with patch("app.services.guardrails.is_emergency", return_value=False), \
         patch("app.services.guardrails.is_symptom_or_diagnosis_request", return_value=True), \
         patch("app.supabase_db.insert_message", new_callable=AsyncMock) as mock_insert_message, \
         patch("app.routes.chat.chat_completion", new_callable=AsyncMock) as mock_chat_completion: # Ensure LLM is not called
        
        payload = {
            "clinic_id": clinic_id,
            "message": "I have a toothache, what should I do?",
            "session_id": "test-symptom-session"
        }
        
        response = client.post("/chat", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["reply"] == expected_reply
        assert data["session_id"] == "test-symptom-session"
        assert data["handoff"] is True
        assert data["handoff_reason"] == "medical_advice_request"
        
        # Verify LLM was NOT called
        mock_chat_completion.assert_not_called()
        # Verify insert_message was called for the assistant's reply
        mock_insert_message.assert_called_once_with("test-symptom-session", "assistant", expected_reply)

def test_chat_endpoint_competitor_guardrail():
    """Test that the competitor guardrail triggers correctly."""
    clinic_id = "smile-city-001"
    clinic_data = DEMO_CLINICS[clinic_id]
    
    expected_reply = (
        f"I can only provide information about {clinic_data.get('clinic_name')}. "
        f"If you have questions about our services, prices, or availability, feel free to ask!"
    )

    # Patch functions where they are used in app.routes.chat
    # Note: We patch app.routes.chat.insert_message because it is imported there
    with patch("app.routes.chat.insert_message", new_callable=AsyncMock) as mock_insert_message, \
         patch("app.routes.chat.log_competitor_query", new_callable=AsyncMock) as mock_log_competitor, \
         patch("app.routes.chat.chat_completion", new_callable=AsyncMock) as mock_chat_completion:
        
        payload = {
            "clinic_id": clinic_id,
            "message": "Is there a better competitor nearby?",
            "session_id": "test-competitor-session"
        }
        
        response = client.post("/chat", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["reply"] == expected_reply
        assert data["session_id"] == "test-competitor-session"
        assert data["handoff"] is False
        
        # Verify LLM was NOT called
        mock_chat_completion.assert_not_called()
        
        # Verify insert_message was called for the assistant's reply (most recent call)
        mock_insert_message.assert_called_with("test-competitor-session", "assistant", expected_reply)
        
        # Verify log_competitor_query was called with correct args
        mock_log_competitor.assert_called_once_with(
            "demo-smile-city", 
            "test-competitor-session", 
            "Is there a better competitor nearby?", 
            "competitor"
        )

def test_feedback_endpoint():
    """Test the feedback submission endpoint."""
    fake_clinic = {"id": "real-clinic-uuid", "clinic_id": "real-clinic"}
    fake_session = {"id": "real-session-uuid"}

    # Patch DB functions to simulate a real clinic interaction
    with patch("app.routes.chat.get_clinic_by_public_id", return_value=fake_clinic), \
         patch("app.routes.chat.get_or_create_session", return_value=fake_session), \
         patch("app.routes.chat.insert_feedback") as mock_insert_feedback:
        
        payload = {
            "clinic_id": "real-clinic",
            "session_id": "user-session-key",
            "rating": "up",
            "comment": "Great service!"
        }
        
        response = client.post("/chat/feedback", json=payload)
        
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        
        # Verify insert_feedback was called with correct arguments
        mock_insert_feedback.assert_called_once_with(
            "real-clinic-uuid",
            "real-session-uuid",
            "up",
            "Great service!"
        )