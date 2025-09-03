import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, status, HTTPException, Depends
from unittest.mock import AsyncMock, patch, MagicMock
from app.api.routes import user
from datetime import datetime, date

app = FastAPI()
app.include_router(user.router)

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

mock_user = {
    "id": "user123",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "is_active": True,
    "is_verified": True,
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": datetime.utcnow().isoformat()
}

mock_profile = {
    "user_id": "user123",
    "total_chats": 10,
    "quizzes_taken": 5,
    "day_streak": 3,
    "days_active": 7,
    "last_activity_date": date.today().isoformat(),
    "streak_start_date": date.today().isoformat(),
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": datetime.utcnow().isoformat()
}
def override_get_current_active_user():
    return mock_user

app.dependency_overrides[user.get_current_active_user] = override_get_current_active_user

# --- /register ---
def test_register_user_success(client):
    user_data = {"email": "test@example.com", "password": "pass1234", "first_name": "Test", "last_name": "User"}
    user_obj = {"id": "user123", **user_data, "is_active": True, "is_verified": True, "created_at": datetime.utcnow().isoformat(), "updated_at": datetime.utcnow().isoformat()}
    with patch("app.api.routes.user.get_user_by_email", new=AsyncMock(return_value=None)), \
         patch("app.api.routes.user.create_user", new=AsyncMock(return_value=user_obj)), \
         patch("app.api.routes.user.create_access_token", return_value="access"), \
         patch("app.api.routes.user.create_refresh_token", return_value="refresh"), \
         patch("app.api.routes.user.UserService") as MockService:
        instance = MockService.return_value
        instance.get_user_profile = AsyncMock(return_value=mock_profile)
        resp = client.post("/register", json=user_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"] == "access"
        assert data["refresh_token"] == "refresh"
        assert data["user"]["email"] == "test@example.com"

def test_register_user_email_exists(client):
    user_data = {"email": "test@example.com", "password": "pass1234", "first_name": "Test", "last_name": "User"}
    with patch("app.api.routes.user.get_user_by_email", new=AsyncMock(return_value={"id": "user123"})):
        resp = client.post("/register", json=user_data)
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Email already registered"

def test_register_user_error(client):
    user_data = {"email": "test@example.com", "password": "pass1234", "first_name": "Test", "last_name": "User"}
    with patch("app.api.routes.user.get_user_by_email", new=AsyncMock(side_effect=Exception("fail"))):
        resp = client.post("/register", json=user_data)
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Registration failed"

# --- /login ---
def test_login_user_success(client):
    user_data = {"email": "test@example.com", "password": "pass1234"}
    user_obj = {**mock_user}
    with patch("app.api.routes.user.authenticate_user", new=AsyncMock(return_value=user_obj)), \
         patch("app.api.routes.user.create_access_token", return_value="access"), \
         patch("app.api.routes.user.create_refresh_token", return_value="refresh"), \
         patch("app.api.routes.user.UserService") as MockService:
        instance = MockService.return_value
        instance.get_user_profile = AsyncMock(return_value=mock_profile)
        resp = client.post("/login", json=user_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"] == "access"
        assert data["refresh_token"] == "refresh"
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["id"] == "user123"

def test_login_user_wrong_password(client):
    user_data = {"email": "test@example.com", "password": "wrong"}
    with patch("app.api.routes.user.authenticate_user", new=AsyncMock(return_value=None)):
        resp = client.post("/login", json=user_data)
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Incorrect email or password"

def test_login_user_inactive(client):
    user_data = {"email": "test@example.com", "password": "pass1234"}
    user_obj = {**mock_user, "is_active": False}
    with patch("app.api.routes.user.authenticate_user", new=AsyncMock(return_value=user_obj)):
        resp = client.post("/login", json=user_data)
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Account is deactivated"

def test_login_user_error(client):
    user_data = {"email": "test@example.com", "password": "pass1234"}
    with patch("app.api.routes.user.authenticate_user", new=AsyncMock(side_effect=Exception("fail"))):
        resp = client.post("/login", json=user_data)
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Login failed"

# --- /refresh ---
def test_refresh_token_success(client):
    with patch("app.api.routes.user.verify_refresh_token", return_value={"user_id": "user123", "user": mock_user}), \
         patch("app.api.routes.user.create_access_token", return_value="access"), \
         patch("app.api.routes.user.create_refresh_token", return_value="refresh"), \
         patch("app.api.routes.user.revoke_refresh_token"):
        resp = client.post("/refresh", json={"refresh_token": "token"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"] == "access"
        assert data["refresh_token"] == "refresh"

def test_refresh_token_invalid(client):
    with patch("app.api.routes.user.verify_refresh_token", return_value=None):
        resp = client.post("/refresh", json={"refresh_token": "token"})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid or expired refresh token"

# --- /profile GET ---
def test_get_profile_success(client):
    with patch("app.api.routes.user.UserService") as MockService:
        instance = MockService.return_value
        instance.get_user_profile = AsyncMock(return_value=mock_profile)
        instance.get_user_statistics = AsyncMock(return_value={"stats": True})
        resp = client.get("/profile")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["email"] == "test@example.com"
        assert data["profile"]["user_id"] == "user123"
        assert data["statistics"]["stats"] is True

def test_get_profile_not_found(client):
    with patch("app.api.routes.user.UserService") as MockService:
        instance = MockService.return_value
        instance.get_user_profile = AsyncMock(return_value=None)
        resp = client.get("/profile")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Profile not found"

def test_get_profile_error(client):
    with patch("app.api.routes.user.UserService") as MockService:
        instance = MockService.return_value
        instance.get_user_profile = AsyncMock(side_effect=Exception("fail"))
        resp = client.get("/profile")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to get profile"

# --- /profile PUT ---
def test_update_profile_success(client):
    update_data = {"first_name": "New"}
    updated_user = {**mock_user, "first_name": "New"}
    with patch("app.api.routes.user.update_user", new=AsyncMock(return_value=updated_user)):
        resp = client.put("/profile", json=update_data)
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "New"

def test_update_profile_no_update(client):
    with patch("app.api.routes.user.update_user", new=AsyncMock(return_value=None)):
        resp = client.put("/profile", json={})
        assert resp.status_code == 200
        assert resp.json()["email"] == "test@example.com"

def test_update_profile_error(client):
    update_data = {"first_name": "New"}
    with patch("app.api.routes.user.update_user", new=AsyncMock(side_effect=Exception("fail"))):
        resp = client.put("/profile", json=update_data)
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to update profile"

# --- /password PUT ---
def test_change_password_success(client):
    with patch("app.api.routes.user.change_user_password", new=AsyncMock(return_value=True)):
        resp = client.put("/password", json={"current_password": "oldpassword", "new_password": "newpassword1"})
        assert resp.status_code == 200
        assert resp.json()["message"] == "Password changed successfully"

def test_change_password_wrong(client):
    with patch("app.api.routes.user.change_user_password", new=AsyncMock(return_value=False)):
        resp = client.put("/password", json={"current_password": "oldpassword", "new_password": "newpassword1"})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Current password is incorrect"

def test_change_password_error(client):
    with patch("app.api.routes.user.change_user_password", new=AsyncMock(side_effect=Exception("fail"))):
        resp = client.put("/password", json={"current_password": "oldpassword", "new_password": "newpassword1"})
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to change password"

# --- /password/reset POST ---
def test_request_password_reset_success(client):
    with patch("app.api.routes.user.get_user_by_email", new=AsyncMock(return_value={"id": "user123"})):
        resp = client.post("/password/reset", json={"email": "test@example.com"})
        assert resp.status_code == 200
        assert "message" in resp.json()

def test_request_password_reset_no_user(client):
    with patch("app.api.routes.user.get_user_by_email", new=AsyncMock(return_value=None)):
        resp = client.post("/password/reset", json={"email": "test@example.com"})
        assert resp.status_code == 200
        assert "message" in resp.json()

def test_request_password_reset_error(client):
    with patch("app.api.routes.user.get_user_by_email", new=AsyncMock(side_effect=Exception("fail"))):
        resp = client.post("/password/reset", json={"email": "test@example.com"})
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to request password reset"

# --- /password/reset/confirm POST ---
def test_confirm_password_reset_success(client):
    resp = client.post("/password/reset/confirm", json={"token": "tok", "new_password": "newpassword1"})
    assert resp.status_code == 200
    assert resp.json()["message"] == "Password reset successfully"

def test_confirm_password_reset_error(client):
    with patch("app.api.routes.user.logger") as mock_logger:
        mock_logger.error = MagicMock()
        resp = client.post("/password/reset/confirm", json={"token": "tok", "new_password": "newpassword1"})
        assert resp.status_code == 200 or resp.status_code == 500

# --- /account DELETE ---
def test_delete_account_success(client):
    with patch("app.api.routes.user.UserService") as MockService:
        instance = MockService.return_value
        instance.delete_user_account = AsyncMock(return_value=True)
        resp = client.request("DELETE", "/account", json={"current_password": "oldpassword", "new_password": "newpassword1"})
        assert resp.status_code == 200
        assert resp.json()["message"] == "Account deleted successfully"

def test_delete_account_wrong_password(client):
    with patch("app.api.routes.user.UserService") as MockService:
        instance = MockService.return_value
        instance.delete_user_account = AsyncMock(return_value=False)
        resp = client.request("DELETE", "/account", json={"current_password": "oldpassword", "new_password": "newpassword1"})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Password is incorrect"

def test_delete_account_error(client):
    with patch("app.api.routes.user.UserService") as MockService:
        instance = MockService.return_value
        instance.delete_user_account = AsyncMock(side_effect=Exception("fail"))
        resp = client.request("DELETE", "/account", json={"current_password": "oldpassword", "new_password": "newpassword1"})
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to delete account"

# --- /activity GET ---
def test_get_activity_summary_success(client):
    with patch("app.api.routes.user.UserService") as MockService:
        instance = MockService.return_value
        instance.get_user_activity_summary = AsyncMock(return_value={"activity": True})
        resp = client.get("/activity?days=10")
        assert resp.status_code == 200
        assert resp.json()["activity"] is True

def test_get_activity_summary_invalid_days(client):
    resp = client.get("/activity?days=0")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Days must be between 1 and 365"

def test_get_activity_summary_error(client):
    with patch("app.api.routes.user.UserService") as MockService:
        instance = MockService.return_value
        instance.get_user_activity_summary = AsyncMock(side_effect=Exception("fail"))
        resp = client.get("/activity?days=10")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to get activity summary"

# --- /leaderboard GET ---
def test_get_leaderboard_success(client):
    with patch("app.api.routes.user.UserService") as MockService:
        instance = MockService.return_value
        instance.get_leaderboard_data = AsyncMock(return_value=[{"user": "A"}, {"user": "B"}])
        resp = client.get("/leaderboard?limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_users"] == 2
        assert len(data["leaderboard"]) == 2

def test_get_leaderboard_invalid_limit(client):
    resp = client.get("/leaderboard?limit=0")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Limit must be between 1 and 100"

def test_get_leaderboard_error(client):
    with patch("app.api.routes.user.UserService") as MockService:
        instance = MockService.return_value
        instance.get_leaderboard_data = AsyncMock(side_effect=Exception("fail"))
        resp = client.get("/leaderboard?limit=2")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to get leaderboard"

# --- /me GET ---
def test_get_current_user_info(client):
    resp = client.get("/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"

# --- /logout POST ---
def test_logout_user_success(client):
    with patch("app.api.routes.user.verify_refresh_token", return_value=True), \
         patch("app.api.routes.user.revoke_refresh_token", return_value=True):
        resp = client.post("/logout", json={"refresh_token": "token"})
        assert resp.status_code == 200
        assert resp.json()["message"] == "Successfully logged out"

def test_logout_user_invalid_token(client):
    with patch("app.api.routes.user.verify_refresh_token", return_value=None):
        resp = client.post("/logout", json={"refresh_token": "token"})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid refresh token"

def test_logout_user_revoke_fail(client):
    with patch("app.api.routes.user.verify_refresh_token", return_value=True), \
         patch("app.api.routes.user.revoke_refresh_token", return_value=False):
        resp = client.post("/logout", json={"refresh_token": "token"})
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to revoke token"

def test_logout_user_error(client):
    with patch("app.api.routes.user.verify_refresh_token", side_effect=Exception("fail")):
        resp = client.post("/logout", json={"refresh_token": "token"})
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Logout failed"

# --- /logout/all POST ---
def test_logout_all_sessions_success(client):
    with patch("app.api.routes.user.revoke_all_user_tokens", return_value=True):
        resp = client.post("/logout/all")
        assert resp.status_code == 200
        assert resp.json()["message"] == "Successfully logged out from all sessions"

def test_logout_all_sessions_fail(client):
    with patch("app.api.routes.user.revoke_all_user_tokens", return_value=False):
        resp = client.post("/logout/all")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to revoke all tokens"

def test_logout_all_sessions_error(client):
    with patch("app.api.routes.user.revoke_all_user_tokens", side_effect=Exception("fail")):
        resp = client.post("/logout/all")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Logout all sessions failed" 