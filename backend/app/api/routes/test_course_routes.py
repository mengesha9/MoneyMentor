import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, status, HTTPException, Depends
from unittest.mock import AsyncMock, patch, MagicMock
from app.api.routes import course

app = FastAPI()
app.include_router(course.router)

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

# --- /start ---
def test_start_course_success(client):
    req = {"user_id": "u1", "session_id": "s1", "course_id": "c1"}
    with patch("app.api.routes.course.CourseService") as MockService:
        instance = MockService.return_value
        instance.start_course = AsyncMock(return_value={"success": True, "message": "Started", "data": {}})
        resp = client.post("/start", json=req)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

def test_start_course_not_found(client):
    req = {"user_id": "u1", "session_id": "s1", "course_id": "c1"}
    with patch("app.api.routes.course.CourseService") as MockService:
        instance = MockService.return_value
        instance.start_course = AsyncMock(side_effect=ValueError("not found"))
        resp = client.post("/start", json=req)
        assert resp.status_code == 404
        assert resp.json()["detail"] == "not found"

def test_start_course_error(client):
    req = {"user_id": "u1", "session_id": "s1", "course_id": "c1"}
    with patch("app.api.routes.course.CourseService") as MockService:
        instance = MockService.return_value
        instance.start_course = AsyncMock(side_effect=Exception("fail"))
        resp = client.post("/start", json=req)
        assert resp.status_code == 500
        assert "Failed to start course" in resp.json()["detail"]

# --- /navigate ---
def test_navigate_course_success(client):
    req = {"user_id": "u1", "session_id": "s1", "course_id": "c1", "page_index": 0}
    with patch("app.api.routes.course.CourseService") as MockService:
        instance = MockService.return_value
        instance.navigate_course_page = AsyncMock(return_value={"success": True, "message": "Nav", "data": {}, "total_pages": 5, "is_last_page": False})
        resp = client.post("/navigate", json=req)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

def test_navigate_course_not_found(client):
    req = {"user_id": "u1", "session_id": "s1", "course_id": "c1", "page_index": 0}
    with patch("app.api.routes.course.CourseService") as MockService:
        instance = MockService.return_value
        instance.navigate_course_page = AsyncMock(side_effect=ValueError("not found"))
        resp = client.post("/navigate", json=req)
        assert resp.status_code == 404
        assert resp.json()["detail"] == "not found"

def test_navigate_course_error(client):
    req = {"user_id": "u1", "session_id": "s1", "course_id": "c1", "page_index": 0}
    with patch("app.api.routes.course.CourseService") as MockService:
        instance = MockService.return_value
        instance.navigate_course_page = AsyncMock(side_effect=Exception("fail"))
        resp = client.post("/navigate", json=req)
        assert resp.status_code == 500
        assert "Failed to navigate course page" in resp.json()["detail"]

# --- /quiz/submit ---
def test_submit_course_quiz_success(client):
    req = {"user_id": "u1", "session_id": "s1", "course_id": "c1", "page_index": 0, "selected_option": "A", "correct": True}
    with patch("app.api.routes.course.CourseService") as MockService:
        instance = MockService.return_value
        instance.submit_course_quiz = AsyncMock(return_value={"success": True, "message": "Quiz", "data": {}, "correct": True, "explanation": "", "next_page": None})
        resp = client.post("/quiz/submit", json=req)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

def test_submit_course_quiz_bad_request(client):
    req = {"user_id": "u1", "session_id": "s1", "course_id": "c1", "page_index": 0, "selected_option": "A", "correct": True}
    with patch("app.api.routes.course.CourseService") as MockService:
        instance = MockService.return_value
        instance.submit_course_quiz = AsyncMock(side_effect=ValueError("bad req"))
        resp = client.post("/quiz/submit", json=req)
        assert resp.status_code == 400
        assert resp.json()["detail"] == "bad req"

def test_submit_course_quiz_error(client):
    req = {"user_id": "u1", "session_id": "s1", "course_id": "c1", "page_index": 0, "selected_option": "A", "correct": True}
    with patch("app.api.routes.course.CourseService") as MockService:
        instance = MockService.return_value
        instance.submit_course_quiz = AsyncMock(side_effect=Exception("fail"))
        resp = client.post("/quiz/submit", json=req)
        assert resp.status_code == 500
        assert "Failed to submit course quiz" in resp.json()["detail"]

# --- /complete ---
def test_complete_course_success(client):
    req = {"user_id": "u1", "session_id": "s1", "course_id": "c1"}
    with patch("app.api.routes.course.CourseService") as MockService:
        instance = MockService.return_value
        instance.complete_course = AsyncMock(return_value={"success": True, "message": "Done", "data": {}})
        resp = client.post("/complete", json=req)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

def test_complete_course_not_found(client):
    req = {"user_id": "u1", "session_id": "s1", "course_id": "c1"}
    with patch("app.api.routes.course.CourseService") as MockService:
        instance = MockService.return_value
        instance.complete_course = AsyncMock(side_effect=ValueError("not found"))
        resp = client.post("/complete", json=req)
        assert resp.status_code == 404
        assert resp.json()["detail"] == "not found"

def test_complete_course_error(client):
    req = {"user_id": "u1", "session_id": "s1", "course_id": "c1"}
    with patch("app.api.routes.course.CourseService") as MockService:
        instance = MockService.return_value
        instance.complete_course = AsyncMock(side_effect=Exception("fail"))
        resp = client.post("/complete", json=req)
        assert resp.status_code == 500
        assert "Failed to complete course" in resp.json()["detail"]

# --- /{course_id} ---
def test_get_course_details_success(client):
    mock_supabase = MagicMock()
    mock_result = MagicMock()
    mock_result.data = [{"id": "c1", "learning_objectives": [], "core_concepts": [], "key_terms": [], "real_life_scenarios": [], "mistakes_to_avoid": [], "action_steps": []}]
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
    with patch("app.api.routes.course.get_supabase", return_value=mock_supabase):
        resp = client.get("/c1")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

def test_get_course_details_not_found(client):
    mock_supabase = MagicMock()
    mock_result = MagicMock()
    mock_result.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
    with patch("app.api.routes.course.get_supabase", return_value=mock_supabase):
        resp = client.get("/c1")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

def test_get_course_details_error(client):
    with patch("app.api.routes.course.get_supabase", side_effect=Exception("fail")):
        resp = client.get("/c1")
        assert resp.status_code == 500
        assert "Failed to get course details" in resp.json()["detail"]

# --- /{course_id}/pages ---
def test_get_course_pages_success(client):
    mock_supabase = MagicMock()
    mock_result = MagicMock()
    mock_result.data = [{"page_index": 0, "content": "..."}]
    mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_result
    with patch("app.api.routes.course.get_supabase", return_value=mock_supabase):
        resp = client.get("/c1/pages")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

def test_get_course_pages_not_found(client):
    mock_supabase = MagicMock()
    mock_result = MagicMock()
    mock_result.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_result
    with patch("app.api.routes.course.get_supabase", return_value=mock_supabase):
        resp = client.get("/c1/pages")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

def test_get_course_pages_error(client):
    with patch("app.api.routes.course.get_supabase", side_effect=Exception("fail")):
        resp = client.get("/c1/pages")
        assert resp.status_code == 500
        assert "Failed to get course pages" in resp.json()["detail"]

# --- /user/{user_id}/sessions ---
def test_get_user_course_sessions_success(client):
    mock_supabase = MagicMock()
    mock_result = MagicMock()
    mock_result.data = [{"session_id": "s1"}]
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
    with patch("app.api.routes.course.get_supabase", return_value=mock_supabase):
        resp = client.get("/user/u1/sessions")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

def test_get_user_course_sessions_error(client):
    with patch("app.api.routes.course.get_supabase", side_effect=Exception("fail")):
        resp = client.get("/user/u1/sessions")
        assert resp.status_code == 500
        assert "Failed to get user course sessions" in resp.json()["detail"] 