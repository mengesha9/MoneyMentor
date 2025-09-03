import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, status, HTTPException, Depends
from unittest.mock import AsyncMock, patch
from app.api.routes import session

app = FastAPI()
app.include_router(session.router)

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

mock_user = {"id": "user123"}
def override_get_current_active_user():
    return mock_user

app.dependency_overrides[session.get_current_active_user] = override_get_current_active_user

# --- /analysis ---
def test_analyze_user_sessions_success(client):
    with patch("app.api.routes.session.get_all_user_sessions", new=AsyncMock(return_value=[{"session_id": "s1", "chat_history": [1,2], "created_at": "2024-01-01"}, {"session_id": "s2", "chat_history": [], "created_at": "2024-01-02"}])), \
         patch("app.api.routes.session.get_recent_user_sessions", new=AsyncMock(return_value=[{"session_id": "s2", "chat_history": []}])):
        resp = client.get("/analysis")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "user123"
        assert data["total_sessions"] == 2
        assert data["sessions_with_chat"] == 1
        assert data["empty_chat_sessions"] == 1
        assert data["total_messages"] == 2

def test_analyze_user_sessions_error(client):
    with patch("app.api.routes.session.get_all_user_sessions", new=AsyncMock(side_effect=Exception("fail"))):
        resp = client.get("/analysis")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "fail"

# --- /cleanup ---
def test_cleanup_user_sessions_success_user_only(client):
    with patch("app.api.routes.session.cleanup_empty_sessions", new=AsyncMock(return_value={"deleted_count": 2, "cutoff_date": "2024-01-01"})):
        resp = client.delete("/cleanup?days_old=10&user_only=true")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["deleted_count"] == 2
        assert data["user_id"] == "user123"

def test_cleanup_user_sessions_success_all_users(client):
    with patch("app.api.routes.session.cleanup_empty_sessions", new=AsyncMock(return_value={"deleted_count": 5, "cutoff_date": "2024-01-01"})):
        resp = client.delete("/cleanup?days_old=10&user_only=false")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["deleted_count"] == 5
        assert data["user_id"] == "all_users"

def test_cleanup_user_sessions_error(client):
    with patch("app.api.routes.session.cleanup_empty_sessions", new=AsyncMock(side_effect=Exception("fail"))):
        resp = client.delete("/cleanup")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "fail"

# --- DELETE /{session_id} ---
def test_delete_user_session_success(client):
    with patch("app.api.routes.session.get_all_user_sessions", new=AsyncMock(return_value=[{"session_id": "s1"}])), \
         patch("app.api.routes.session.delete_session", new=AsyncMock(return_value=True)):
        resp = client.delete("/s1")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

def test_delete_user_session_not_found(client):
    with patch("app.api.routes.session.get_all_user_sessions", new=AsyncMock(return_value=[])):
        resp = client.delete("/s1")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Session not found or access denied"

def test_delete_user_session_delete_fail(client):
    with patch("app.api.routes.session.get_all_user_sessions", new=AsyncMock(return_value=[{"session_id": "s1"}])), \
         patch("app.api.routes.session.delete_session", new=AsyncMock(return_value=False)):
        resp = client.delete("/s1")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to delete session"

def test_delete_user_session_error(client):
    with patch("app.api.routes.session.get_all_user_sessions", new=AsyncMock(side_effect=Exception("fail"))):
        resp = client.delete("/s1")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "fail"

# --- /recent ---
def test_get_recent_sessions_success(client):
    with patch("app.api.routes.session.get_recent_user_sessions", new=AsyncMock(return_value=[{"session_id": "s1"}, {"session_id": "s2"}])):
        resp = client.get("/recent?hours=12")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "user123"
        assert data["count"] == 2
        assert data["hours_back"] == 12

def test_get_recent_sessions_error(client):
    with patch("app.api.routes.session.get_recent_user_sessions", new=AsyncMock(side_effect=Exception("fail"))):
        resp = client.get("/recent")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "fail" 