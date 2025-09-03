import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, status, HTTPException, Depends
from unittest.mock import AsyncMock, patch, MagicMock
from app.api.routes import quiz

app = FastAPI()
app.include_router(quiz.router)

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

mock_user = {"id": "user123"}
def override_get_current_active_user():
    return mock_user

app.dependency_overrides[quiz.get_current_active_user] = override_get_current_active_user

# --- /generate ---
def test_generate_quiz_diagnostic_success(client):
    req = {"session_id": "sess1", "quiz_type": "diagnostic", "topic": "Investing", "difficulty": "easy"}
    with patch("app.api.routes.quiz.get_session", new=AsyncMock(return_value={"session_id": "sess1", "chat_history": []})), \
         patch("app.api.routes.quiz.QuizService") as MockService:
        instance = MockService.return_value
        instance.generate_diagnostic_quiz = AsyncMock(return_value=[{"question": "Q?", "choices": {"a": "A"}, "correct_answer": "a", "explanation": "E", "topic": "Investing", "difficulty": "easy"}])
        resp = client.post("/generate", json=req)
        assert resp.status_code == 200
        data = resp.json()
        assert data["quiz_type"] == "diagnostic"
        assert data["questions"][0]["question"] == "Q?"

def test_generate_quiz_micro_success(client):
    req = {"session_id": "sess1", "quiz_type": "micro", "difficulty": "medium"}
    with patch("app.api.routes.quiz.get_session", new=AsyncMock(return_value={"session_id": "sess1", "chat_history": [{"role": "user", "content": "topic"}]})), \
         patch("app.api.routes.quiz.QuizService") as MockService:
        instance = MockService.return_value
        instance.extract_topic_from_message = MagicMock(return_value="topic")
        instance.generate_quiz_from_history = AsyncMock(return_value=[{"question": "Q?", "choices": {"a": "A"}, "correct_answer": "a", "explanation": "E"}])
        resp = client.post("/generate", json=req)
        assert resp.status_code == 200
        data = resp.json()
        assert data["quiz_type"] == "micro"
        assert data["questions"][0]["question"] == "Q?"

def test_generate_quiz_error(client):
    req = {"session_id": "sess1", "quiz_type": "diagnostic", "topic": "Investing"}
    with patch("app.api.routes.quiz.get_session", new=AsyncMock(side_effect=Exception("fail"))):
        resp = client.post("/generate", json=req)
        assert resp.status_code == 500
        assert "Failed to generate quiz" in resp.json()["detail"]

# --- /submit ---
def test_submit_quiz_success(client):
    req = {
        "user_id": "user123", 
        "quiz_type": "micro", 
        "session_id": "test_session_123",
        "responses": [
            {
                "quiz_id": "q1", 
                "selected_option": "A", 
                "correct": True, 
                "topic": "Investing"
            }
        ]
    }
    with patch("app.api.routes.quiz.get_supabase") as mock_supabase, \
         patch("app.api.routes.quiz._update_user_progress_from_batch", new=AsyncMock(return_value=True)), \
         patch.object(quiz, "google_sheets_service", MagicMock(service=True)):
        mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value = MagicMock()
        resp = client.post("/submit", json=req)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

def test_submit_quiz_error(client):
    req = {"user_id": "user123", "quiz_type": "micro", "responses": [{"quiz_id": "q1", "selected_option": "A", "correct": True, "topic": "Investing"}]}
    with patch("app.api.routes.quiz.get_supabase", side_effect=Exception("fail")):
        resp = client.post("/submit", json=req)
        assert resp.status_code == 500
        assert "Failed to submit quiz responses" in resp.json()["detail"]

def test_submit_quiz_creates_session_if_not_exists(client):
    """Test that quiz submission creates a session if it doesn't exist"""
    req = {
        "user_id": "user123", 
        "quiz_type": "micro", 
        "session_id": "new_session_123",
        "responses": [
            {
                "quiz_id": "q1", 
                "selected_option": "A", 
                "correct": True, 
                "topic": "Investing"
            }
        ]
    }
    
    with patch("app.api.routes.quiz.get_supabase") as mock_supabase, \
         patch("app.api.routes.quiz._update_user_progress_from_batch", new=AsyncMock(return_value=True)), \
         patch.object(quiz, "google_sheets_service", MagicMock(service=True)):
        
        # Mock the table method to return different mocks for different tables
        mock_table = MagicMock()
        mock_supabase.return_value.table = mock_table
        
        # Mock session check - first call returns empty (session doesn't exist)
        # Second call returns session data (session was created)
        mock_select = MagicMock()
        mock_eq = MagicMock()
        mock_execute = MagicMock()
        
        mock_table.return_value.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.side_effect = [
            MagicMock(data=[]),  # Session doesn't exist
            MagicMock(data=[{"session_id": "new_session_123"}])  # Session was created
        ]
        
        # Mock insert operations
        mock_table.return_value.insert.return_value.execute.return_value = MagicMock()
        
        resp = client.post("/submit", json=req)
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        
        # Verify that session creation was attempted
        # The table should be called with "user_sessions" for session creation
        # and "quiz_responses" for quiz submission
        mock_table.assert_any_call("user_sessions")
        mock_table.assert_any_call("quiz_responses")

def test_submit_quiz_with_existing_session(client):
    """Test that quiz submission works with existing session"""
    req = {
        "user_id": "user123", 
        "quiz_type": "micro", 
        "session_id": "existing_session_123",
        "responses": [
            {
                "quiz_id": "q1", 
                "selected_option": "A", 
                "correct": True, 
                "topic": "Investing"
            }
        ]
    }
    
    with patch("app.api.routes.quiz.get_supabase") as mock_supabase, \
         patch("app.api.routes.quiz._update_user_progress_from_batch", new=AsyncMock(return_value=True)), \
         patch.object(quiz, "google_sheets_service", MagicMock(service=True)):
        
        # Mock session check - session exists
        mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"session_id": "existing_session_123"}]
        )
        
        # Mock insert operations
        mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value = MagicMock()
        
        resp = client.post("/submit", json=req)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

def test_submit_quiz_stores_all_details(client):
    """Test that quiz submission stores all quiz details including explanation, correct_answer, question_data"""
    req = {
        "user_id": "user123", 
        "quiz_type": "micro", 
        "session_id": "test_session_123",
        "responses": [
            {
                "quiz_id": "quiz_test_123",
                "selected_option": "A", 
                "correct": True, 
                "topic": "Investing",
                "explanation": "This is the explanation for the correct answer",
                "correct_answer": "A",
                "question_data": {
                    "question": "What is the best investment strategy?",
                    "choices": {"a": "Diversify", "b": "Put all in one stock", "c": "Avoid investing", "d": "Only cash"},
                    "correct_answer": "A",
                    "explanation": "This is the explanation for the correct answer",
                    "topic": "Investing",
                    "difficulty": "medium"
                }
            }
        ]
    }
    
    with patch("app.api.routes.quiz.get_supabase") as mock_supabase, \
         patch("app.api.routes.quiz._update_user_progress_from_batch", new=AsyncMock(return_value=True)), \
         patch.object(quiz, "google_sheets_service", MagicMock(service=True)):
        
        # Mock successful submission
        mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value = MagicMock()
        
        resp = client.post("/submit", json=req)
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        
        # Verify that the insert was called with all the expected fields
        mock_supabase.return_value.table.assert_called_with('quiz_responses')
        insert_call = mock_supabase.return_value.table.return_value.insert.call_args[0][0]
        
        # Check that all fields are present in the insert data
        quiz_response = insert_call[0]
        assert quiz_response["user_id"] == "user123"
        assert quiz_response["quiz_id"] == "quiz_test_123"
        assert quiz_response["topic"] == "Investing"
        assert quiz_response["selected"] == "A"
        assert quiz_response["correct"] is True
        assert quiz_response["quiz_type"] == "micro"
        assert quiz_response["score"] == 100.0
        assert quiz_response["explanation"] == "This is the explanation for the correct answer"
        assert quiz_response["correct_answer"] == "A"
        assert quiz_response["question_data"] == {
            "question": "What is the best investment strategy?",
            "choices": {"a": "Diversify", "b": "Put all in one stock", "c": "Avoid investing", "d": "Only cash"},
            "correct_answer": "A",
            "explanation": "This is the explanation for the correct answer",
            "topic": "Investing",
            "difficulty": "medium"
        }
        assert quiz_response["session_id"] == "test_session_123"

def test_submit_diagnostic_quiz_stores_all_details(client):
    """Test that diagnostic quiz submission stores all quiz details including explanation, correct_answer, question_data"""
    req = {
        "user_id": "user123", 
        "quiz_type": "diagnostic", 
        "responses": [
            {
                "quiz_id": "quiz_diagnostic_123",
                "selected_option": "A", 
                "correct": True, 
                "topic": "Investing",
                "explanation": "This is the explanation for the correct answer",
                "correct_answer": "A",
                "question_data": {
                    "question": "What is the best investment strategy?",
                    "choices": ["Diversify", "Put all in one stock", "Avoid investing", "Only cash"],
                    "correct_answer": "A",
                    "explanation": "This is the explanation for the correct answer",
                    "topic": "Investing",
                    "difficulty": "medium"
                }
            },
            {
                "quiz_id": "quiz_diagnostic_123",
                "selected_option": "B", 
                "correct": False, 
                "topic": "Budgeting",
                "explanation": "This is the explanation for the correct answer",
                "correct_answer": "A",
                "question_data": {
                    "question": "What is budgeting?",
                    "choices": ["Spending without limits", "Tracking income and expenses", "Ignoring bills", "Gambling"],
                    "correct_answer": "A",
                    "explanation": "This is the explanation for the correct answer",
                    "topic": "Budgeting",
                    "difficulty": "easy"
                }
            }
        ]
    }
    
    with patch("app.api.routes.quiz.get_supabase") as mock_supabase, \
         patch("app.api.routes.quiz._update_user_progress_from_batch", new=AsyncMock(return_value=True)), \
         patch.object(quiz, "google_sheets_service", MagicMock(service=True)):
        
        # Mock successful submission
        mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value = MagicMock()
        
        resp = client.post("/submit", json=req)
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        
        # Verify that the insert was called with all the expected fields
        # For diagnostic quizzes, both quiz_responses and courses tables may be called
        mock_supabase.return_value.table.assert_any_call('quiz_responses')
        
        # Get the quiz_responses insert call specifically
        insert_calls = mock_supabase.return_value.table.call_args_list
        quiz_responses_call = None
        for call in insert_calls:
            if call[0][0] == 'quiz_responses':
                quiz_responses_call = call
                break
        
        assert quiz_responses_call is not None, "quiz_responses table was not called"
        
        # Get the insert call for quiz_responses
        insert_call = mock_supabase.return_value.table.return_value.insert.call_args[0][0]
        
        # Check that all fields are present in the insert data for both responses
        assert len(insert_call) == 2
        
        # First response
        quiz_response_1 = insert_call[0]
        assert quiz_response_1["user_id"] == "user123"
        assert quiz_response_1["quiz_id"] == "quiz_diagnostic_123"
        assert quiz_response_1["topic"] == "Investing"
        assert quiz_response_1["selected"] == "A"
        assert quiz_response_1["correct"] is True
        assert quiz_response_1["quiz_type"] == "diagnostic"
        assert quiz_response_1["score"] == 100.0
        assert quiz_response_1["explanation"] == "This is the explanation for the correct answer"
        assert quiz_response_1["correct_answer"] == "A"
        assert quiz_response_1["question_data"] == {
            "question": "What is the best investment strategy?",
            "choices": ["Diversify", "Put all in one stock", "Avoid investing", "Only cash"],
            "correct_answer": "A",
            "explanation": "This is the explanation for the correct answer",
            "topic": "Investing",
            "difficulty": "medium"
        }
        
        # Second response
        quiz_response_2 = insert_call[1]
        assert quiz_response_2["user_id"] == "user123"
        assert quiz_response_2["quiz_id"] == "quiz_diagnostic_123"
        assert quiz_response_2["topic"] == "Budgeting"
        assert quiz_response_2["selected"] == "B"
        assert quiz_response_2["correct"] is False
        assert quiz_response_2["quiz_type"] == "diagnostic"
        assert quiz_response_2["score"] == 0.0
        assert quiz_response_2["explanation"] == "This is the explanation for the correct answer"
        assert quiz_response_2["correct_answer"] == "A"
        assert quiz_response_2["question_data"] == {
            "question": "What is budgeting?",
            "choices": ["Spending without limits", "Tracking income and expenses", "Ignoring bills", "Gambling"],
            "correct_answer": "A",
            "explanation": "This is the explanation for the correct answer",
            "topic": "Budgeting",
            "difficulty": "easy"
        }

# --- /history ---
def test_get_quiz_history_success(client):
    mock_supabase = MagicMock()
    mock_result = MagicMock()
    mock_result.data = [{"quiz_type": "micro"}]
    mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_result
    with patch("app.api.routes.quiz.get_supabase", return_value=mock_supabase):
        resp = client.get("/history")
        assert resp.status_code == 200
        assert resp.json()["user_id"] == "user123"

def test_get_quiz_history_error(client):
    with patch("app.api.routes.quiz.get_supabase", side_effect=Exception("fail")):
        resp = client.get("/history")
        assert resp.status_code == 500
        assert "Failed to get quiz history" in resp.json()["detail"]

# --- /history/session/{session_id} ---
def test_get_session_quiz_history_success(client):
    mock_supabase = MagicMock()
    mock_result = MagicMock()
    mock_result.data = [{"quiz_type": "micro"}]
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = mock_result
    with patch("app.api.routes.quiz.get_supabase", return_value=mock_supabase):
        resp = client.get("/history/session/sess1")
        assert resp.status_code == 200
        assert resp.json()["session_id"] == "sess1"

def test_get_session_quiz_history_error(client):
    with patch("app.api.routes.quiz.get_supabase", side_effect=Exception("fail")):
        resp = client.get("/history/session/sess1")
        assert resp.status_code == 500
        assert "Failed to get session micro quiz history" in resp.json()["detail"]

def test_submit_and_retrieve_quiz_from_session_history(client):
    """Test that a submitted quiz can be retrieved from session history"""
    session_id = "test_session_123"
    user_id = "user123"
    quiz_type = "micro"

    # Mock data for quiz submission
    submit_req = {
        "user_id": user_id,
        "quiz_type": quiz_type,
        "responses": [
            {
                "quiz_id": f"quiz_{session_id}_1234567890.123",
                "selected_option": "A",
                "correct": True,
                "topic": "Investing"
            },
            {
                "quiz_id": f"quiz_{session_id}_1234567890.124",
                "selected_option": "B",
                "correct": False,
                "topic": "Budgeting"
            }
        ]
    }

    # Mock data for quiz history retrieval (without session_id column)
    mock_quiz_history = [
        {
            "id": "1",
            "user_id": user_id,
            "quiz_type": quiz_type,
            "quiz_id": f"quiz_{session_id}_1234567890.123",
            "selected": "A",
            "correct": True,
            "topic": "Investing",
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": "2",
            "user_id": user_id,
            "quiz_type": quiz_type,
            "quiz_id": f"quiz_{session_id}_1234567890.124",
            "selected": "B",
            "correct": False,
            "topic": "Budgeting",
            "created_at": "2024-01-01T00:00:01Z"
        }
    ]

    # Test quiz submission
    with patch("app.api.routes.quiz.get_supabase") as mock_supabase, \
         patch("app.api.routes.quiz._update_user_progress_from_batch", new=AsyncMock(return_value=True)), \
         patch.object(quiz, "google_sheets_service", MagicMock(service=True)):

        # Mock successful submission
        mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value = MagicMock()

        submit_resp = client.post("/submit", json=submit_req)
        assert submit_resp.status_code == 200
        assert submit_resp.json()["success"] is True

        # Reset mock for history retrieval
        mock_supabase.reset_mock()

        # Test quiz history retrieval for the same session
        mock_result = MagicMock()
        mock_result.data = mock_quiz_history

        # Configure the mock for the new query chain with like() instead of eq() for session_id
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_like = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_order = MagicMock()
        mock_execute = MagicMock()

        mock_supabase.return_value.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.like.return_value = mock_like
        mock_like.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.order.return_value = mock_order
        mock_order.execute.return_value = mock_result

        history_resp = client.get(f"/history/session/{session_id}")
        assert history_resp.status_code == 200

        history_data = history_resp.json()
        assert history_data["session_id"] == session_id
        assert history_data["user_id"] == user_id
        assert len(history_data["quiz_history"]) == 2

        # Verify the submitted quiz responses are in the history
        responses = history_data["quiz_history"]
        assert responses[0]["quiz_id"] == f"quiz_{session_id}_1234567890.123"
        assert responses[0]["selected"] == "A"
        assert responses[0]["correct"] is True
        assert responses[0]["topic"] == "Investing"

        assert responses[1]["quiz_id"] == f"quiz_{session_id}_1234567890.124"
        assert responses[1]["selected"] == "B"
        assert responses[1]["correct"] is False
        assert responses[1]["topic"] == "Budgeting"

# --- /history/course/{course_id} ---
def test_get_course_quiz_history_success(client):
    mock_supabase = MagicMock()
    mock_result = MagicMock()
    mock_result.data = [{"correct": True}]
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = mock_result
    with patch("app.api.routes.quiz.get_supabase", return_value=mock_supabase):
        resp = client.get("/history/course/c1")
        assert resp.status_code == 200
        assert resp.json()["course_id"] == "c1"

def test_get_course_quiz_history_error(client):
    with patch("app.api.routes.quiz.get_supabase", side_effect=Exception("fail")):
        resp = client.get("/history/course/c1")
        assert resp.status_code == 500
        assert "Failed to get course quiz history" in resp.json()["detail"]

# --- /session/ ---
def test_create_new_session_success(client):
    with patch("app.api.routes.quiz.create_session", new=AsyncMock(return_value={"session_id": "sess1", "user_id": "user123"})):
        resp = client.post("/session/")
        assert resp.status_code == 200
        assert resp.json()["session_id"] == "sess1" 

# --- /progress/session/{session_id} ---
def test_get_session_quiz_progress_success(client):
    """Test getting session-specific quiz progress"""
    session_id = "test_session_123"
    user_id = "user123"

    # Mock quiz responses for this session (without session_id column)
    mock_quiz_responses = [
        {
            "id": "1",
            "user_id": user_id,
            "quiz_type": "micro",
            "quiz_id": f"quiz_{session_id}_1234567890.123",
            "selected": "A",
            "correct": True,
            "topic": "Investing",
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": "2",
            "user_id": user_id,
            "quiz_type": "micro",
            "quiz_id": f"quiz_{session_id}_1234567890.124",
            "selected": "B",
            "correct": False,
            "topic": "Budgeting",
            "created_at": "2024-01-01T00:00:01Z"
        },
        {
            "id": "3",
            "user_id": user_id,
            "quiz_type": "micro",
            "quiz_id": f"quiz_{session_id}_1234567890.125",
            "selected": "C",
            "correct": True,
            "topic": "Saving",
            "created_at": "2024-01-01T00:00:02Z"
        }
    ]

    with patch("app.api.routes.quiz.get_supabase") as mock_supabase:
        mock_result = MagicMock()
        mock_result.data = mock_quiz_responses
        # Mock the new query chain with like() instead of eq() for session_id
        mock_supabase.return_value.table.return_value.select.return_value.like.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        resp = client.get(f"/progress/session/{session_id}")
        assert resp.status_code == 200

        data = resp.json()
        assert data["session_id"] == session_id
        assert data["user_id"] == user_id
        assert data["correct_answers"] == 2  # 2 correct out of 3
        assert data["total_quizzes"] == 3
        assert data["score_percentage"] == 66.67  # 2/3 * 100

def test_get_session_quiz_progress_empty(client):
    """Test getting session quiz progress when no quizzes exist"""
    session_id = "empty_session_123"
    user_id = "user123"
    
    with patch("app.api.routes.quiz.get_supabase") as mock_supabase:
        mock_result = MagicMock()
        mock_result.data = []  # No quiz responses
        # Mock the new query chain with like() instead of eq() for session_id
        mock_supabase.return_value.table.return_value.select.return_value.like.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result
        
        resp = client.get(f"/progress/session/{session_id}")
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["session_id"] == session_id
        assert data["user_id"] == user_id
        assert data["correct_answers"] == 0
        assert data["total_quizzes"] == 0
        assert data["score_percentage"] == 0.0

def test_get_session_quiz_progress_error(client):
    """Test getting session quiz progress when database error occurs"""
    session_id = "error_session_123"
    
    with patch("app.api.routes.quiz.get_supabase", side_effect=Exception("Database error")):
        resp = client.get(f"/progress/session/{session_id}")
        assert resp.status_code == 500
        assert "Failed to get session quiz progress" in resp.json()["detail"]

def test_get_session_quiz_progress_all_correct(client):
    """Test getting session quiz progress when all answers are correct"""
    session_id = "perfect_session_123"
    user_id = "user123"

    # Mock quiz responses with all correct answers (without session_id column)
    mock_quiz_responses = [
        {
            "id": "1",
            "user_id": user_id,
            "quiz_type": "micro",
            "quiz_id": f"quiz_{session_id}_1234567890.123",
            "selected": "A",
            "correct": True,
            "topic": "Investing",
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": "2",
            "user_id": user_id,
            "quiz_type": "micro",
            "quiz_id": f"quiz_{session_id}_1234567890.124",
            "selected": "B",
            "correct": True,
            "topic": "Budgeting",
            "created_at": "2024-01-01T00:00:01Z"
        }
    ]

    with patch("app.api.routes.quiz.get_supabase") as mock_supabase:
        mock_result = MagicMock()
        mock_result.data = mock_quiz_responses
        # Mock the new query chain with like() instead of eq() for session_id
        mock_supabase.return_value.table.return_value.select.return_value.like.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        resp = client.get(f"/progress/session/{session_id}")
        assert resp.status_code == 200

        data = resp.json()
        assert data["session_id"] == session_id
        assert data["user_id"] == user_id
        assert data["correct_answers"] == 2
        assert data["total_quizzes"] == 2
        assert data["score_percentage"] == 100.0  # 2/2 * 100

def test_get_session_quiz_progress_all_incorrect(client):
    """Test getting session quiz progress when all answers are incorrect"""
    session_id = "failed_session_123"
    user_id = "user123"

    # Mock quiz responses with all incorrect answers (without session_id column)
    mock_quiz_responses = [
        {
            "id": "1",
            "user_id": user_id,
            "quiz_type": "micro",
            "quiz_id": f"quiz_{session_id}_1234567890.123",
            "selected": "A",
            "correct": False,
            "topic": "Investing",
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": "2",
            "user_id": user_id,
            "quiz_type": "micro",
            "quiz_id": f"quiz_{session_id}_1234567890.124",
            "selected": "B",
            "correct": False,
            "topic": "Budgeting",
            "created_at": "2024-01-01T00:00:01Z"
        }
    ]

    with patch("app.api.routes.quiz.get_supabase") as mock_supabase:
        mock_result = MagicMock()
        mock_result.data = mock_quiz_responses
        # Mock the new query chain with like() instead of eq() for session_id
        mock_supabase.return_value.table.return_value.select.return_value.like.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        resp = client.get(f"/progress/session/{session_id}")
        assert resp.status_code == 200

        data = resp.json()
        assert data["session_id"] == session_id
        assert data["user_id"] == user_id
        assert data["correct_answers"] == 0
        assert data["total_quizzes"] == 2
        assert data["score_percentage"] == 0.0  # 0/2 * 100 

def test_session_quiz_history_returns_all_details(client):
    """Test that session quiz history returns all quiz details including explanation, correct_answer, question_data"""
    session_id = "test_session_123"
    user_id = "user123"

    # Mock quiz responses with all details
    mock_quiz_responses = [
        {
            "id": "1",
            "user_id": user_id,
            "quiz_type": "micro",
            "quiz_id": f"quiz_{session_id}_1234567890.123",
            "selected": "A",
            "correct": True,
            "topic": "Investing",
            "explanation": "This is the explanation for the correct answer",
            "correct_answer": "A",
            "question_data": {
                "question": "What is the best investment strategy?",
                "choices": {"a": "Diversify", "b": "Put all in one stock", "c": "Avoid investing", "d": "Only cash"},
                "correct_answer": "A",
                "explanation": "This is the explanation for the correct answer",
                "topic": "Investing",
                "difficulty": "medium"
            },
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]

    with patch("app.api.routes.quiz.get_supabase") as mock_supabase:
        mock_result = MagicMock()
        mock_result.data = mock_quiz_responses
        # Mock the new query chain with like() instead of eq() for session_id
        mock_supabase.return_value.table.return_value.select.return_value.like.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = mock_result

        resp = client.get(f"/history/session/{session_id}")
        assert resp.status_code == 200

        data = resp.json()
        assert data["session_id"] == session_id
        assert data["user_id"] == user_id
        assert len(data["quiz_history"]) == 1

        # Verify that all quiz details are returned
        quiz_response = data["quiz_history"][0]
        assert quiz_response["id"] == "1"
        assert quiz_response["user_id"] == user_id
        assert quiz_response["quiz_type"] == "micro"
        assert quiz_response["quiz_id"] == f"quiz_{session_id}_1234567890.123"
        assert quiz_response["selected"] == "A"
        assert quiz_response["correct"] is True
        assert quiz_response["topic"] == "Investing"
        assert quiz_response["explanation"] == "This is the explanation for the correct answer"
        assert quiz_response["correct_answer"] == "A"
        assert quiz_response["question_data"] == {
            "question": "What is the best investment strategy?",
            "choices": {"a": "Diversify", "b": "Put all in one stock", "c": "Avoid investing", "d": "Only cash"},
            "correct_answer": "A",
            "explanation": "This is the explanation for the correct answer",
            "topic": "Investing",
            "difficulty": "medium"
        } 