import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, status, HTTPException, Depends
from unittest.mock import AsyncMock, patch, MagicMock
from app.api.routes import chat
from app.models.schemas import ChatMessageRequest
import types
import uuid

app = FastAPI()
app.include_router(chat.router)

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

# Helper: default user and request
mock_user = {"id": "550e8400-e29b-41d4-a716-446655440000"}
def override_get_current_active_user():
    return mock_user

app.dependency_overrides[chat.get_current_active_user] = override_get_current_active_user

valid_chat_request = {"query": "Hello!", "session_id": "550e8400-e29b-41d4-a716-446655440000"}

# --- /message ---
def test_process_message_success(client):
    with patch("app.api.routes.chat.ChatService") as MockService:
        instance = MockService.return_value
        instance.process_message = AsyncMock(return_value={"message": "Hi!"})
        resp = client.post("/message", json=valid_chat_request)
        assert resp.status_code == 200
        assert resp.json()["message"] == "Hi!"

def test_process_message_invalid_response(client):
    with patch("app.api.routes.chat.ChatService") as MockService:
        instance = MockService.return_value
        instance.process_message = AsyncMock(return_value="not a dict")
        resp = client.post("/message", json=valid_chat_request)
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Invalid response format"

def test_process_message_missing_message(client):
    with patch("app.api.routes.chat.ChatService") as MockService:
        instance = MockService.return_value
        instance.process_message = AsyncMock(return_value={})
        resp = client.post("/message", json=valid_chat_request)
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Missing message in response"

def test_process_message_exception(client):
    with patch("app.api.routes.chat.ChatService") as MockService:
        instance = MockService.return_value
        instance.process_message = AsyncMock(side_effect=Exception("fail"))
        resp = client.post("/message", json=valid_chat_request)
        assert resp.status_code == 500
        assert resp.json()["detail"] == "fail"

async def async_gen_tokens(tokens):
    for t in tokens:
        yield t

# --- /message/stream ---
def test_process_message_streaming_success(client):
    # Patch all async dependencies and streaming response
    with patch("app.api.routes.chat.get_session", new=AsyncMock(return_value={"session_id": "550e8400-e29b-41d4-a716-446655440000", "chat_history": []})), \
         patch("app.api.routes.chat.money_mentor_function.process_and_stream", new=AsyncMock(return_value=MagicMock(body_iterator=async_gen_tokens([b"token1", b"token2"]), headers={}))), \
         patch("app.api.routes.chat.ChatService") as MockService:
        instance = MockService.return_value
        instance._handle_background_tasks_only = AsyncMock()
        resp = client.post("/message/stream", json=valid_chat_request)
        assert resp.status_code == 200
        assert b"token1" in resp.content or b"token2" in resp.content

def test_process_message_streaming_session_creation(client):
    # Simulate no session found, so create_session is called
    with patch("app.api.routes.chat.get_session", new=AsyncMock(return_value=None)), \
         patch("app.api.routes.chat.create_session", new=AsyncMock(return_value={"session_id": "550e8400-e29b-41d4-a716-446655440000", "chat_history": []})), \
         patch("app.api.routes.chat.money_mentor_function.process_and_stream", new=AsyncMock(return_value=MagicMock(body_iterator=async_gen_tokens([b"token1"]), headers={}))), \
         patch("app.api.routes.chat.ChatService") as MockService:
        instance = MockService.return_value
        instance._handle_background_tasks_only = AsyncMock()
        resp = client.post("/message/stream", json=valid_chat_request)
        assert resp.status_code == 200
        assert b"token1" in resp.content

def test_process_message_streaming_error(client):
    with patch("app.api.routes.chat.get_session", new=AsyncMock(side_effect=Exception("fail"))):
        resp = client.post("/message/stream", json=valid_chat_request)
        assert resp.status_code == 200
        assert b"error" in resp.content

# --- NEW EDGE CASE TESTS ---

def test_process_message_streaming_with_dummy_session_id(client):
    """Test handling of 'dummy' session ID - should create new session"""
    dummy_request = {"query": "Hello!", "session_id": "dummy"}
    
    with patch("app.api.routes.chat.get_session", new=AsyncMock(return_value=None)), \
         patch("app.api.routes.chat.create_session", new=AsyncMock(return_value={"session_id": "new-uuid-123", "chat_history": []})), \
         patch("app.api.routes.chat.money_mentor_function.process_and_stream", new=AsyncMock(return_value=MagicMock(body_iterator=async_gen_tokens([b"response"]), headers={}))), \
         patch("app.api.routes.chat.ChatService") as MockService:
        instance = MockService.return_value
        instance._handle_background_tasks_only = AsyncMock()
        resp = client.post("/message/stream", json=dummy_request)
        assert resp.status_code == 200
        assert b"response" in resp.content

def test_process_message_streaming_with_invalid_uuid(client):
    """Test handling of invalid UUID format session ID"""
    invalid_request = {"query": "Hello!", "session_id": "invalid-uuid-format"}
    
    with patch("app.api.routes.chat.get_session", new=AsyncMock(side_effect=Exception("invalid input syntax for type uuid"))):
        resp = client.post("/message/stream", json=invalid_request)
        assert resp.status_code == 200
        assert b"error" in resp.content

def test_process_message_streaming_with_nonexistent_session(client):
    """Test handling of session ID that doesn't exist in database"""
    nonexistent_request = {"query": "Hello!", "session_id": "550e8400-e29b-41d4-a716-446655440000"}
    
    with patch("app.api.routes.chat.get_session", new=AsyncMock(return_value=None)), \
         patch("app.api.routes.chat.create_session", new=AsyncMock(return_value={"session_id": "550e8400-e29b-41d4-a716-446655440000", "chat_history": []})), \
         patch("app.api.routes.chat.money_mentor_function.process_and_stream", new=AsyncMock(return_value=MagicMock(body_iterator=async_gen_tokens([b"response"]), headers={}))), \
         patch("app.api.routes.chat.ChatService") as MockService:
        instance = MockService.return_value
        instance._handle_background_tasks_only = AsyncMock()
        resp = client.post("/message/stream", json=nonexistent_request)
        assert resp.status_code == 200
        assert b"response" in resp.content

def test_process_message_streaming_update_existing_session(client):
    """Test updating chat history of existing session"""
    existing_session = {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "chat_history": [
            {"role": "user", "content": "Previous message", "timestamp": "2024-01-01T00:00:00"}
        ]
    }
    
    with patch("app.api.routes.chat.get_session", new=AsyncMock(return_value=existing_session)), \
         patch("app.api.routes.chat.update_session", new=AsyncMock(return_value=None)), \
         patch("app.api.routes.chat.money_mentor_function.process_and_stream", new=AsyncMock(return_value=MagicMock(body_iterator=async_gen_tokens([b"updated response"]), headers={}))), \
         patch("app.api.routes.chat.ChatService") as MockService:
        instance = MockService.return_value
        instance._handle_background_tasks_only = AsyncMock()
        resp = client.post("/message/stream", json=valid_chat_request)
        assert resp.status_code == 200
        assert b"updated response" in resp.content

def test_process_message_streaming_database_error(client):
    """Test handling of database errors during session operations"""
    with patch("app.api.routes.chat.get_session", new=AsyncMock(side_effect=Exception("Database connection failed"))):
        resp = client.post("/message/stream", json=valid_chat_request)
        assert resp.status_code == 200
        assert b"error" in resp.content

def test_process_message_streaming_create_session_failure(client):
    """Test handling of session creation failure"""
    with patch("app.api.routes.chat.get_session", new=AsyncMock(return_value=None)), \
         patch("app.api.routes.chat.create_session", new=AsyncMock(side_effect=Exception("Failed to create session"))):
        resp = client.post("/message/stream", json=valid_chat_request)
        assert resp.status_code == 200
        assert b"error" in resp.content

def test_process_message_streaming_with_empty_query(client):
    """Test handling of empty query"""
    empty_request = {"query": "", "session_id": "550e8400-e29b-41d4-a716-446655440000"}
    
    resp = client.post("/message/stream", json=empty_request)
    assert resp.status_code == 422  # Validation error

def test_process_message_streaming_with_missing_session_id(client):
    """Test handling of missing session_id"""
    missing_session_request = {"query": "Hello!"}
    
    resp = client.post("/message/stream", json=missing_session_request)
    assert resp.status_code == 422  # Validation error

def test_process_message_streaming_with_null_session_id(client):
    """Test handling of null session_id"""
    null_session_request = {"query": "Hello!", "session_id": None}
    
    resp = client.post("/message/stream", json=null_session_request)
    assert resp.status_code == 422  # Validation error

def test_process_message_streaming_with_very_long_session_id(client):
    """Test handling of extremely long session_id"""
    long_session_request = {"query": "Hello!", "session_id": "a" * 1000}
    
    with patch("app.api.routes.chat.get_session", new=AsyncMock(side_effect=Exception("Session ID too long"))):
        resp = client.post("/message/stream", json=long_session_request)
        assert resp.status_code == 200
        assert b"error" in resp.content

def test_process_message_streaming_concurrent_sessions(client):
    """Test handling multiple concurrent sessions"""
    session1_request = {"query": "Hello from session 1", "session_id": "550e8400-e29b-41d4-a716-446655440000"}
    session2_request = {"query": "Hello from session 2", "session_id": "660e8400-e29b-41d4-a716-446655440001"}
    
    # Test first session
    with patch("app.api.routes.chat.get_session", new=AsyncMock(return_value={"session_id": "550e8400-e29b-41d4-a716-446655440000", "chat_history": []})), \
         patch("app.api.routes.chat.money_mentor_function.process_and_stream", new=AsyncMock(return_value=MagicMock(body_iterator=async_gen_tokens([b"response1"]), headers={}))), \
         patch("app.api.routes.chat.ChatService") as MockService:
        instance = MockService.return_value
        instance._handle_background_tasks_only = AsyncMock()
        resp1 = client.post("/message/stream", json=session1_request)
        assert resp1.status_code == 200
        assert b"response1" in resp1.content
    
    # Test second session
    with patch("app.api.routes.chat.get_session", new=AsyncMock(return_value={"session_id": "660e8400-e29b-41d4-a716-446655440001", "chat_history": []})), \
         patch("app.api.routes.chat.money_mentor_function.process_and_stream", new=AsyncMock(return_value=MagicMock(body_iterator=async_gen_tokens([b"response2"]), headers={}))), \
         patch("app.api.routes.chat.ChatService") as MockService:
        instance = MockService.return_value
        instance._handle_background_tasks_only = AsyncMock()
        resp2 = client.post("/message/stream", json=session2_request)
        assert resp2.status_code == 200
        assert b"response2" in resp2.content

# --- /history/{session_id} ---
def test_get_chat_history_success(client):
    with patch("app.api.routes.chat.get_session", new=AsyncMock(return_value={"session_id": "550e8400-e29b-41d4-a716-446655440000", "chat_history": [
        {"role": "user", "content": "Hi", "timestamp": "2024-01-01T00:00:00"}
    ]})):
        resp = client.get("/history/550e8400-e29b-41d4-a716-446655440000")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert data["message_count"] == 1

def test_get_chat_history_not_found(client):
    with patch("app.api.routes.chat.get_session", new=AsyncMock(return_value=None)):
        resp = client.get("/history/550e8400-e29b-41d4-a716-446655440000")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Session not found"

def test_get_chat_history_exception(client):
    with patch("app.api.routes.chat.get_session", new=AsyncMock(side_effect=Exception("fail"))):
        resp = client.get("/history/550e8400-e29b-41d4-a716-446655440000")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "fail"

# --- /history/{session_id} DELETE ---
def test_clear_chat_history_success(client):
    with patch("app.api.routes.chat.get_session", new=AsyncMock(return_value={"session_id": "550e8400-e29b-41d4-a716-446655440000"})), \
         patch("app.api.routes.chat.update_session", new=AsyncMock(return_value=None)):
        resp = client.delete("/history/550e8400-e29b-41d4-a716-446655440000")
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

def test_clear_chat_history_not_found(client):
    with patch("app.api.routes.chat.get_session", new=AsyncMock(return_value=None)):
        resp = client.delete("/history/550e8400-e29b-41d4-a716-446655440000")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Session not found"

def test_clear_chat_history_exception(client):
    with patch("app.api.routes.chat.get_session", new=AsyncMock(side_effect=Exception("fail"))):
        resp = client.delete("/history/550e8400-e29b-41d4-a716-446655440000")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "fail"

# --- /session/{session_id} DELETE ---
def test_delete_chat_session_success(client):
    with patch("app.api.routes.chat.get_session", new=AsyncMock(return_value={"session_id": "550e8400-e29b-41d4-a716-446655440000", "user_id": "550e8400-e29b-41d4-a716-446655440000"})), \
         patch("app.api.routes.chat.delete_session", new=AsyncMock(return_value=True)):
        resp = client.delete("/session/550e8400-e29b-41d4-a716-446655440000")
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

def test_delete_chat_session_not_found(client):
    with patch("app.api.routes.chat.get_session", new=AsyncMock(return_value=None)):
        resp = client.delete("/session/550e8400-e29b-41d4-a716-446655440000")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Session not found"

def test_delete_chat_session_forbidden(client):
    with patch("app.api.routes.chat.get_session", new=AsyncMock(return_value={"session_id": "550e8400-e29b-41d4-a716-446655440000", "user_id": "otheruser"})):
        resp = client.delete("/session/550e8400-e29b-41d4-a716-446655440000")
        assert resp.status_code == 403
        assert resp.json()["detail"] == "Access denied - session does not belong to current user"

def test_delete_chat_session_exception(client):
    with patch("app.api.routes.chat.get_session", new=AsyncMock(side_effect=Exception("fail"))):
        resp = client.delete("/session/550e8400-e29b-41d4-a716-446655440000")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "fail"

# --- /history/ (all user sessions) ---
def test_get_all_user_sessions_success(client):
    with patch("app.api.routes.chat.get_all_user_sessions", new=AsyncMock(return_value=[
        {"session_id": "550e8400-e29b-41d4-a716-446655440000", "chat_history": [{"role": "user", "content": "Hi", "timestamp": "2024-01-01T00:00:00"}]},
        {"session_id": "660e8400-e29b-41d4-a716-446655440001", "chat_history": [{"role": "assistant", "content": "Hello", "timestamp": "2024-01-01T00:00:01"}]}
    ])):
        resp = client.get("/history/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["total_sessions"] == 2
        assert data["total_messages"] == 2
        assert data["user_id"] == "550e8400-e29b-41d4-a716-446655440000"

def test_get_all_user_sessions_empty(client):
    with patch("app.api.routes.chat.get_all_user_sessions", new=AsyncMock(return_value=[])):
        resp = client.get("/history/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["total_sessions"] == 0
        assert data["total_messages"] == 0

def test_get_all_user_sessions_exception(client):
    with patch("app.api.routes.chat.get_all_user_sessions", new=AsyncMock(side_effect=Exception("fail"))):
        resp = client.get("/history/")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "fail" 

# --- /session/{session_id}/chat-count ---
def test_get_session_chat_count_success(client):
    """Test getting session chat count with messages"""
    session_id = "test_session_123"
    user_id = "550e8400-e29b-41d4-a716-446655440000"  # Match the mock user ID
    
    # Mock session with chat history
    mock_session = {
        "session_id": session_id,
        "user_id": user_id,
        "chat_history": [
            {"role": "user", "content": "Hello", "timestamp": "2024-01-01T00:00:00"},
            {"role": "assistant", "content": "Hi there!", "timestamp": "2024-01-01T00:00:01"},
            {"role": "user", "content": "How are you?", "timestamp": "2024-01-01T00:00:02"},
            {"role": "assistant", "content": "I'm doing well!", "timestamp": "2024-01-01T00:00:03"},
            {"role": "user", "content": "What's the weather?", "timestamp": "2024-01-01T00:00:04"}
        ]
    }
    
    with patch("app.api.routes.chat.get_session", new=AsyncMock(return_value=mock_session)):
        resp = client.get(f"/session/{session_id}/chat-count")
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["session_id"] == session_id
        assert data["user_id"] == user_id
        assert data["chat_count"] == 3  # 3 user messages
        assert data["should_generate_quiz"] is True  # 3 messages >= 3
        assert data["messages_until_quiz"] == 0  # Already at 3 messages

def test_get_session_chat_count_below_threshold(client):
    """Test getting session chat count when below quiz threshold"""
    session_id = "test_session_456"
    user_id = "550e8400-e29b-41d4-a716-446655440000"  # Match the mock user ID
    
    # Mock session with fewer messages
    mock_session = {
        "session_id": session_id,
        "user_id": user_id,
        "chat_history": [
            {"role": "user", "content": "Hello", "timestamp": "2024-01-01T00:00:00"},
            {"role": "assistant", "content": "Hi there!", "timestamp": "2024-01-01T00:00:01"},
            {"role": "user", "content": "How are you?", "timestamp": "2024-01-01T00:00:02"}
        ]
    }
    
    with patch("app.api.routes.chat.get_session", new=AsyncMock(return_value=mock_session)):
        resp = client.get(f"/session/{session_id}/chat-count")
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["session_id"] == session_id
        assert data["user_id"] == user_id
        assert data["chat_count"] == 2  # 2 user messages
        assert data["should_generate_quiz"] is False  # 2 messages < 3
        assert data["messages_until_quiz"] == 1  # Need 1 more message

def test_get_session_chat_count_no_messages(client):
    """Test getting session chat count with no messages"""
    session_id = "test_session_789"
    user_id = "550e8400-e29b-41d4-a716-446655440000"  # Match the mock user ID
    
    # Mock session with no chat history
    mock_session = {
        "session_id": session_id,
        "user_id": user_id,
        "chat_history": []
    }
    
    with patch("app.api.routes.chat.get_session", new=AsyncMock(return_value=mock_session)):
        resp = client.get(f"/session/{session_id}/chat-count")
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["session_id"] == session_id
        assert data["user_id"] == user_id
        assert data["chat_count"] == 0  # No user messages
        assert data["should_generate_quiz"] is False  # 0 messages < 3
        assert data["messages_until_quiz"] == 3  # Need 3 more messages

def test_get_session_chat_count_session_not_found(client):
    """Test getting session chat count when session doesn't exist"""
    session_id = "nonexistent_session"
    
    with patch("app.api.routes.chat.get_session", new=AsyncMock(return_value=None)):
        resp = client.get(f"/session/{session_id}/chat-count")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Session not found"

def test_get_session_chat_count_error(client):
    """Test getting session chat count when database error occurs"""
    session_id = "error_session"
    
    with patch("app.api.routes.chat.get_session", new=AsyncMock(side_effect=Exception("Database error"))):
        resp = client.get(f"/session/{session_id}/chat-count")
        assert resp.status_code == 500
        assert "Failed to get session chat count" in resp.json()["detail"]

def test_get_session_chat_count_mixed_messages(client):
    """Test getting session chat count with mixed user and assistant messages"""
    session_id = "test_session_mixed"
    user_id = "550e8400-e29b-41d4-a716-446655440000"  # Match the mock user ID
    
    # Mock session with mixed message types
    mock_session = {
        "session_id": session_id,
        "user_id": user_id,
        "chat_history": [
            {"role": "assistant", "content": "Welcome!", "timestamp": "2024-01-01T00:00:00"},
            {"role": "user", "content": "Hello", "timestamp": "2024-01-01T00:00:01"},
            {"role": "assistant", "content": "Hi there!", "timestamp": "2024-01-01T00:00:02"},
            {"role": "user", "content": "How are you?", "timestamp": "2024-01-01T00:00:03"},
            {"role": "assistant", "content": "I'm doing well!", "timestamp": "2024-01-01T00:00:04"},
            {"role": "user", "content": "What's the weather?", "timestamp": "2024-01-01T00:00:05"},
            {"role": "assistant", "content": "It's sunny!", "timestamp": "2024-01-01T00:00:06"},
            {"role": "user", "content": "Great!", "timestamp": "2024-01-01T00:00:07"}
        ]
    }
    
    with patch("app.api.routes.chat.get_session", new=AsyncMock(return_value=mock_session)):
        resp = client.get(f"/session/{session_id}/chat-count")
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["session_id"] == session_id
        assert data["user_id"] == user_id
        assert data["chat_count"] == 4  # 4 user messages
        assert data["should_generate_quiz"] is True  # 4 messages >= 3
        assert data["messages_until_quiz"] == 0  # Already above threshold 