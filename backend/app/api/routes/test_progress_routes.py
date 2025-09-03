import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, status, HTTPException
from unittest.mock import AsyncMock, patch, MagicMock
from app.api.routes import progress

app = FastAPI()
app.include_router(progress.router)

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

# --- /user/{user_id} ---
def test_get_user_progress_success(client):
    with patch("app.api.routes.progress.money_mentor_crew.create_progress_crew") as mock_crew:
        crew_instance = MagicMock()
        crew_instance.kickoff.return_value = {
            "user_id": "u1",
            "total_chats": 10,
            "quizzes_taken": 5,
            "correct_answers": 4,
            "topics_covered": ["Investing"],
            "last_activity": "2024-01-01T00:00:00Z"
        }
        mock_crew.return_value = crew_instance
        resp = client.get("/user/u1")
        assert resp.status_code == 200
        assert resp.json()["user_id"] == "u1"

def test_get_user_progress_error(client):
    with patch("app.api.routes.progress.money_mentor_crew.create_progress_crew", side_effect=Exception("fail")):
        resp = client.get("/user/u1")
        assert resp.status_code == 500
        assert "Failed to get user progress" in resp.json()["detail"]

# --- /analytics/{user_id} ---
def test_get_learning_analytics_success(client):
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"quiz_type": "micro", "correct": True}])
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"chat_history": [{"msg": "hi"}]}])
    with patch("app.api.routes.progress.get_supabase", return_value=mock_supabase), \
         patch("app.api.routes.progress.money_mentor_crew.create_progress_crew") as mock_crew:
        crew_instance = MagicMock()
        crew_instance.kickoff.return_value = {"ai": "analysis"}
        mock_crew.return_value = crew_instance
        resp = client.get("/analytics/u1")
        assert resp.status_code == 200
        assert resp.json()["user_id"] == "u1"
        assert "quiz_performance" in resp.json()
        assert "ai_analysis" in resp.json()

def test_get_learning_analytics_error(client):
    with patch("app.api.routes.progress.get_supabase", side_effect=Exception("fail")):
        resp = client.get("/analytics/u1")
        assert resp.status_code == 500
        assert "Failed to get learning analytics" in resp.json()["detail"]

# --- /leaderboard ---
def test_get_leaderboard_success(client):
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.execute.return_value = MagicMock(data=[{"user_id": "u1", "correct": True}, {"user_id": "u1", "correct": False}, {"user_id": "u2", "correct": True}])
    with patch("app.api.routes.progress.get_supabase", return_value=mock_supabase):
        resp = client.get("/leaderboard")
        assert resp.status_code == 200
        assert "leaderboard" in resp.json()
        assert resp.json()["total_users"] == 2

def test_get_leaderboard_error(client):
    with patch("app.api.routes.progress.get_supabase", side_effect=Exception("fail")):
        resp = client.get("/leaderboard")
        assert resp.status_code == 500
        assert "Failed to get leaderboard" in resp.json()["detail"]

# --- /export-all-users ---
def test_export_all_user_profiles_success(client):
    with patch("app.services.google_sheets_service.GoogleSheetsService") as MockService:
        instance = MockService.return_value
        instance.get_all_user_profiles_for_export = AsyncMock(return_value=[{"user_id": "u1"}])
        instance.export_user_profiles_to_sheet = AsyncMock(return_value=True)
        resp = client.post("/export-all-users")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

def test_export_all_user_profiles_none(client):
    with patch("app.services.google_sheets_service.GoogleSheetsService") as MockService:
        instance = MockService.return_value
        instance.get_all_user_profiles_for_export = AsyncMock(return_value=[])
        resp = client.post("/export-all-users")
        assert resp.status_code == 200
        assert resp.json()["success"] is False

def test_export_all_user_profiles_error(client):
    with patch("app.services.google_sheets_service.GoogleSheetsService", side_effect=Exception("fail")):
        resp = client.post("/export-all-users")
        assert resp.status_code == 500
        assert "Failed to export user profiles" in resp.json()["detail"]

# --- /export/{user_id} ---
def test_export_user_data_success(client):
    with patch("app.services.google_sheets_service.GoogleSheetsService") as MockService, \
         patch("app.api.routes.progress.get_supabase") as mock_supabase:
        instance = MockService.return_value
        instance.export_user_profiles_to_sheet = AsyncMock(return_value=True)
        mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data={"user_id": "u1", "total_chats": 10, "quizzes_taken": 5, "day_streak": 2, "days_active": 7})
        mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data={"first_name": "Test", "last_name": "User", "email": "test@example.com"})
        resp = client.post("/export/u1")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

def test_export_user_data_profile_not_found(client):
    with patch("app.services.google_sheets_service.GoogleSheetsService") as MockService, \
         patch("app.api.routes.progress.get_supabase") as mock_supabase:
        instance = MockService.return_value
        instance.export_user_profiles_to_sheet = AsyncMock(return_value=True)
        mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data=None)
        resp = client.post("/export/u1")
        assert resp.status_code == 404
        assert "User profile not found" in resp.json()["detail"]

def test_export_user_data_user_not_found(client):
    with patch("app.services.google_sheets_service.GoogleSheetsService") as MockService, \
         patch("app.api.routes.progress.get_supabase") as mock_supabase:
        instance = MockService.return_value
        instance.export_user_profiles_to_sheet = AsyncMock(return_value=True)
        # First call returns profile, second call returns None for user
        mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = [MagicMock(data={"user_id": "u1"}), MagicMock(data=None)]
        resp = client.post("/export/u1")
        assert resp.status_code == 404
        assert "User not found" in resp.json()["detail"]

def test_export_user_data_error(client):
    with patch("app.services.google_sheets_service.GoogleSheetsService", side_effect=Exception("fail")):
        resp = client.post("/export/u1")
        assert resp.status_code == 500
        assert "Failed to export user data" in resp.json()["detail"] 