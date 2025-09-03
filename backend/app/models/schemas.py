from pydantic import BaseModel, Field, UUID4, field_validator, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum
import uuid

class QuizType(str, Enum):
    DIAGNOSTIC = "diagnostic"
    MICRO = "micro"

class ChatMessage(BaseModel):
    message: str = Field(..., description="User message")
    user_id: str = Field(..., description="Unique user identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Bot response")
    session_id: str = Field(..., description="Session identifier")
    should_show_quiz: bool = Field(False, description="Whether to show a quiz")
    quiz_data: Optional[Dict[str, Any]] = Field(None, description="Quiz data if applicable")
    calculation_result: Optional[Dict[str, Any]] = Field(None, description="Calculation result if applicable")

class QuizQuestion(BaseModel):
    question: str = Field(..., description="Question text")
    choices: Dict[str, str] = Field(..., description="Multiple choice options with keys a, b, c, d")
    correct_answer: str = Field(..., description="Correct answer key (a, b, c, or d)")
    explanation: str = Field(..., description="Explanation for the correct answer")
    topic: Optional[str] = Field(None, description="Topic of the question")
    difficulty: Optional[str] = Field(None, description="Difficulty level of the question (easy, medium, hard)")

class QuizRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    quiz_type: QuizType = Field(..., description="Type of quiz")
    topic: Optional[str] = Field(None, description="Topic of the quiz")
    difficulty: Optional[str] = Field("medium", description="Quiz difficulty level")

class QuizResponse(BaseModel):
    questions: List[QuizQuestion] = Field(..., description="List of quiz questions")
    quiz_id: str = Field(..., description="Unique quiz identifier")
    quiz_type: QuizType = Field(..., description="Type of quiz")
    topic: Optional[str] = Field(None, description="Topic of the quiz")
class QuizAttempt(BaseModel):
    user_id: str = Field(..., description="User identifier")
    quiz_id: str = Field(..., description="Quiz identifier")
    question_id: str = Field(..., description="Question identifier")
    selected_option: int = Field(..., description="Selected answer index")
    topic_tag: str = Field(..., description="Question topic")

class QuizAttemptResponse(BaseModel):
    correct: bool = Field(..., description="Whether answer was correct")
    explanation: str = Field(..., description="Explanation of the correct answer")
    correct_answer: int = Field(..., description="Index of correct answer")

class QuizSubmission(BaseModel):
    """Schema for quiz response submission"""
    user_id: str = Field(..., description="User identifier")
    quiz_id: str = Field(..., description="Quiz identifier")
    selected_option: str = Field(..., description="Selected answer (A, B, C, or D)", pattern="^[A-D]$")
    correct: bool = Field(..., description="Whether the answer was correct")
    topic: str = Field(..., description="Quiz topic")
    quiz_type: str = Field("micro", description="Type of quiz (micro, diagnostic, etc.)")
    
    @field_validator('selected_option')
    @classmethod
    def validate_selected_option(cls, v):
        if v not in ['A', 'B', 'C', 'D']:
            raise ValueError('selected_option must be A, B, C, or D')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "quiz_id": "quiz456",
                "selected_option": "B",
                "correct": True,
                "topic": "Investing",
                "quiz_type": "micro"
            }
        }

class QuizSubmissionBatch(BaseModel):
    """Schema for submitting multiple quiz responses at once"""
    quiz_type: str = Field("micro", description="Type of quiz (micro, diagnostic, etc.)")
    session_id: Optional[str] = Field(None, description="Session identifier for tracking")
    responses: List[Dict[str, Any]] = Field(..., description="List of quiz responses")
    user_id: Optional[str] = Field(None, description="User identifier (optional, can be derived from token)")
    selected_course_type: Optional[str] = Field(None, description="Selected course type for personalized course generation")
    
    @field_validator('responses')
    @classmethod
    def validate_responses(cls, v):
        if not v:
            raise ValueError('responses list cannot be empty')
        
        for i, response in enumerate(v):
            required_fields = ['quiz_id', 'selected_option', 'correct', 'topic']
            for field in required_fields:
                if field not in response:
                    raise ValueError(f'Response {i} missing required field: {field}')
            
            # Validate selected_option
            selected = response.get('selected_option')
            if selected not in ['A', 'B', 'C', 'D']:
                raise ValueError(f'Response {i} selected_option must be A, B, C, or D')
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "quiz_type": "diagnostic",
                "responses": [
                    {
                        "quiz_id": "quiz_1",
                        "selected_option": "B",
                        "correct": True,
                        "topic": "Investing"
                    },
                    {
                        "quiz_id": "quiz_2", 
                        "selected_option": "A",
                        "correct": False,
                        "topic": "Budgeting"
                    }
                ]
            }
        }

class CalculationRequest(BaseModel):
    """Schema for calculation requests - matches client requirements exactly"""
    calculation_type: str = Field(..., description="Type of calculation (credit_card_payoff, savings_goal, student_loan)")
    principal: Optional[float] = Field(None, description="Principal amount for loans/credit cards")
    interest_rate: float = Field(..., description="Annual interest rate (as percentage)")
    target_months: Optional[int] = Field(None, description="Target months for payoff/savings")
    monthly_payment: Optional[float] = Field(None, description="Monthly payment amount")
    target_amount: Optional[float] = Field(None, description="Target savings amount")
    
    class Config:
        json_schema_extra = {
            "example": {
                "calculation_type": "credit_card_payoff",
                "principal": 6000,
                "interest_rate": 22.0,
                "target_months": 12,
                "monthly_payment": None
            }
        }

class CalculationResult(BaseModel):
    """Schema for calculation results - matches client requirements exactly"""
    monthly_payment: Optional[float] = Field(None, description="Required monthly payment")
    months_to_payoff: Optional[int] = Field(None, description="Months to complete payoff")
    total_interest: float = Field(..., description="Total interest paid/earned")
    step_by_step_plan: List[str] = Field(..., description="Array of strings with step-by-step plan")
    total_amount: float = Field(..., description="Total amount paid/saved")
    
    class Config:
        json_schema_extra = {
            "example": {
                "monthly_payment": 567.89,
                "months_to_payoff": 12,
                "total_interest": 814.68,
                "step_by_step_plan": [
                    "Starting balance: $6,000.00",
                    "APR: 22% (monthly rate: 1.83%)",
                    "Monthly payment: $567.89",
                    "Month 1: Pay $456.23 principal, $111.66 interest",
                    "Remaining balance after month 1: $5,543.77",
                    "Continue this pattern for 12 months",
                    "Total interest paid: $814.68",
                    "Total amount paid: $6,814.68"
                ],
                "total_amount": 6814.68
            }
        }

class UserSession(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    session_id: str = Field(..., description="Session identifier")
    chat_count: int = Field(0, description="Number of chat interactions")
    last_quiz_at: Optional[datetime] = Field(None, description="Last quiz timestamp")
    diagnostic_completed: bool = Field(False, description="Whether diagnostic quiz is completed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ProgressData(BaseModel):
    user_id: str = Field(..., description="User identifier")
    total_chats: int = Field(..., description="Total chat interactions")
    quizzes_taken: int = Field(..., description="Number of quizzes taken")
    correct_answers: int = Field(..., description="Number of correct answers")
    topics_covered: List[str] = Field(..., description="Topics discussed")
    last_activity: datetime = Field(..., description="Last activity timestamp")

class ContentDocument(BaseModel):
    """Schema for content document metadata"""
    file_id: str
    filename: str
    content_type: str
    uploaded_at: datetime
    status: str
    title: Optional[str] = None
    description: Optional[str] = None
    topic: Optional[str] = None

class SearchRequest(BaseModel):
    """Schema for content search requests"""
    query: str
    limit: Optional[int] = 5
    threshold: Optional[float] = 0.7
    filters: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    """Schema for content search responses"""
    results: List[Dict[str, Any]]
    total: int
    query: str
    filters: Optional[Dict[str, Any]] = None

class TopicCreate(BaseModel):
    """Schema for creating a new topic"""
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None

class TopicResponse(BaseModel):
    """Schema for topic responses"""
    id: str
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class AIGeneratedCourse(BaseModel):
    """Schema for AI-generated course with 10 pages of content"""
    title: str = Field(..., description="Course title")
    pages: List[Dict[str, str]] = Field(..., description="List of 10 course pages, each with title and content (max 500 chars per page)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Beginner Budgeting Basics",
                "pages": [
                    {"title": "What is Budgeting?", "content": "Budgeting is a plan for your money..."},
                    {"title": "The 50/30/20 Rule", "content": "This popular method divides your income..."},
                    {"title": "Tracking Your Expenses", "content": "Keep track of where your money goes..."},
                    {"title": "Setting Financial Goals", "content": "Define what you want to achieve..."},
                    {"title": "Creating Your First Budget", "content": "Step-by-step guide to build your budget..."},
                    {"title": "Sticking to Your Budget", "content": "Tips and strategies for success..."},
                    {"title": "Adjusting Your Budget", "content": "How to modify your plan when needed..."},
                    {"title": "Budgeting Tools", "content": "Apps and methods to help you stay organized..."},
                    {"title": "Common Budgeting Mistakes", "content": "Avoid these pitfalls on your journey..."},
                    {"title": "Your Budgeting Journey", "content": "Reflect on what you've learned..."}
                ]
            }
        }

class CourseRecommendation(BaseModel):
    """Schema for course recommendation based on diagnostic results following student lesson template"""
    title: str = Field(..., description="Course title")
    module: str = Field(..., description="Module name")
    track: str = Field(..., description="Track (e.g., 'High School')")
    estimated_length: str = Field(..., description="Estimated course length (e.g., '2,000-2,500 words')")
    lesson_overview: str = Field(..., description="Brief overview explaining why the lesson matters and what students will learn")
    learning_objectives: List[str] = Field(..., description="List of key learning objectives")
    core_concepts: List[Dict[str, str]] = Field(..., description="List of core concepts with title, explanation, metaphor, and quick_challenge")
    key_terms: List[Dict[str, str]] = Field(..., description="List of key terms with term, definition, and example")
    real_life_scenarios: List[Dict[str, str]] = Field(..., description="List of real-life scenarios with title and narrative")
    mistakes_to_avoid: List[str] = Field(..., description="List of common misconceptions or financial mistakes")
    action_steps: List[str] = Field(..., description="List of step-by-step actions students can try")
    summary: str = Field(..., description="Wrap-up paragraph reinforcing the lesson takeaway")
    reflection_prompt: str = Field(..., description="Journal-style question for student reflection")
    sample_quiz: List[Dict[str, Any]] = Field(..., description="List of sample quiz questions with options, correct answer, and explanation")
    course_level: str = Field(..., description="Course difficulty level (beginner/intermediate/advanced)")
    why_recommended: str = Field(..., description="Explanation of why this course was recommended")
    has_quiz: bool = Field(..., description="Whether the course includes a quiz section")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Intermediate Risk Management",
                "module": "Investment Fundamentals",
                "track": "High School",
                "estimated_length": "2,000-2,500 words",
                "lesson_overview": "This lesson will help you master risk management concepts that are essential for making smart investment decisions. You'll learn practical strategies that connect directly to real-life money situations you'll face.",
                "learning_objectives": [
                    "Understand different types of investment risks",
                    "Learn risk mitigation strategies",
                    "Build a balanced portfolio"
                ],
                "core_concepts": [
                    {
                        "title": "Understanding Investment Risk",
                        "explanation": "Investment risk is the possibility of losing money on an investment. Different investments have different levels of risk.",
                        "metaphor": "Think of it like crossing a street - some crossings are safer than others!",
                        "quick_challenge": "What's one risky financial decision you've seen someone make?"
                    }
                ],
                "key_terms": [
                    {
                        "term": "Risk Management",
                        "definition": "The practice of identifying and minimizing potential losses",
                        "example": "Diversifying your investments across different types of assets"
                    }
                ],
                "real_life_scenarios": [
                    {
                        "title": "Maria's First Investment",
                        "narrative": "Maria, a high school student, wanted to invest her summer job savings. She researched different options and chose a mix of stocks and bonds to balance risk and potential returns."
                    }
                ],
                "mistakes_to_avoid": [
                    "Putting all your money in one investment",
                    "Ignoring the risk level of investments"
                ],
                "action_steps": [
                    "Research different investment types",
                    "Create a simple investment plan",
                    "Start with small amounts to learn"
                ],
                "summary": "You've taken an important step toward understanding risk management. Remember, every investment decision involves balancing risk and potential reward.",
                "reflection_prompt": "What's one investment risk you want to understand better?",
                "sample_quiz": [
                    {
                        "question": "What is the main benefit of diversifying your investments?",
                        "options": {
                            "a": "It guarantees higher returns",
                            "b": "It reduces overall risk",
                            "c": "It's required by law",
                            "d": "It doesn't matter"
                        },
                        "correct_answer": "b",
                        "explanation": "Diversification spreads risk across different investments, reducing the chance of losing everything."
                    }
                ],
                "course_level": "intermediate",
                "why_recommended": "Based on your 65% diagnostic score and identified weaknesses in risk management concepts.",
                "has_quiz": True
            }
        }

class ChatMessageRequest(BaseModel):
    """Schema for chat message request"""
    query: str = Field(..., min_length=1, description="The user's query (cannot be empty)")
    session_id: str = Field(..., min_length=1, description="Session identifier (any string, not restricted to UUID v4)")
    
    @field_validator('query')
    @classmethod
    def validate_query_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('query cannot be empty or whitespace only')
        return v.strip()
    
    @field_validator('session_id')
    @classmethod
    def validate_session_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('session_id cannot be empty or whitespace only')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is compound interest?",
                "session_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }

# Course-related schemas
class CoursePage(BaseModel):
    """Schema for a single course page"""
    id: Optional[str] = Field(None, description="Page ID")
    page_index: int = Field(..., description="Page index (0-based)")
    title: str = Field(..., description="Page title")
    content: str = Field(..., description="Page content")
    page_type: str = Field("content", description="Page type: content, quiz, summary")
    quiz_data: Optional[Dict[str, Any]] = Field(None, description="Quiz data for quiz pages")

class Course(BaseModel):
    """Schema for a course"""
    id: Optional[str] = Field(None, description="Course ID")
    title: str = Field(..., description="Course title")
    module: str = Field(..., description="Module name")
    track: str = Field(..., description="Track (e.g., 'High School')")
    estimated_length: str = Field(..., description="Estimated course length")
    lesson_overview: str = Field(..., description="Brief overview")
    learning_objectives: List[str] = Field(..., description="List of learning objectives")
    core_concepts: List[Dict[str, str]] = Field(..., description="List of core concepts")
    key_terms: List[Dict[str, str]] = Field(..., description="List of key terms")
    real_life_scenarios: List[Dict[str, str]] = Field(..., description="List of real-life scenarios")
    mistakes_to_avoid: List[str] = Field(..., description="List of mistakes to avoid")
    action_steps: List[str] = Field(..., description="List of action steps")
    summary: str = Field(..., description="Course summary")
    reflection_prompt: str = Field(..., description="Reflection prompt")
    course_level: str = Field("beginner", description="Course difficulty level")
    why_recommended: str = Field(..., description="Why this course was recommended")
    has_quiz: bool = Field(True, description="Whether the course includes quizzes")
    topic: str = Field(..., description="Course topic")
    pages: Optional[List[CoursePage]] = Field(None, description="Course pages")

class CourseSession(BaseModel):
    """Schema for user course session"""
    id: Optional[str] = Field(None, description="Session ID")
    user_id: str = Field(..., description="User ID")
    course_id: str = Field(..., description="Course ID")
    current_page_index: int = Field(0, description="Current page index")
    completed: bool = Field(False, description="Whether course is completed")
    started_at: Optional[datetime] = Field(None, description="When course was started")
    completed_at: Optional[datetime] = Field(None, description="When course was completed")
    quiz_answers: Dict[str, Any] = Field(default_factory=dict, description="Quiz answers")

class CourseStartRequest(BaseModel):
    """Schema for starting a course"""
    user_id: str = Field(..., description="User ID")
    session_id: str = Field(..., description="Session ID")
    course_id: str = Field(..., description="Course ID")

class CourseStartResponse(BaseModel):
    """Schema for course start response"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    current_page: Optional[CoursePage] = Field(None, description="Current page")
    course_session: Optional[CourseSession] = Field(None, description="Course session")

class CourseNavigateRequest(BaseModel):
    """Schema for navigating course pages"""
    user_id: str = Field(..., description="User ID")
    session_id: str = Field(..., description="Session ID")
    course_id: str = Field(..., description="Course ID")
    page_index: int = Field(..., description="Target page index")

class CourseNavigateResponse(BaseModel):
    """Schema for course navigation response"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    current_page: Optional[CoursePage] = Field(None, description="Current page")
    total_pages: int = Field(..., description="Total number of pages")
    is_last_page: bool = Field(..., description="Whether this is the last page")

class CourseQuizSubmitRequest(BaseModel):
    """Schema for submitting course quiz answers"""
    user_id: str = Field(..., description="User ID")
    session_id: str = Field(..., description="Session ID")
    course_id: str = Field(..., description="Course ID")
    page_index: int = Field(..., description="Page index")
    selected_option: str = Field(..., description="Selected answer (A, B, C, or D)")
    correct: bool = Field(..., description="Whether the answer was correct")

class CourseQuizSubmitResponse(BaseModel):
    """Schema for course quiz submission response"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    correct: bool = Field(..., description="Whether the answer was correct")
    explanation: str = Field(..., description="Explanation for the answer")
    next_page: Optional[CoursePage] = Field(None, description="Next page if available")

class CourseCompleteRequest(BaseModel):
    """Schema for completing a course"""
    user_id: str = Field(..., description="User ID")
    session_id: str = Field(..., description="Session ID")
    course_id: str = Field(..., description="Course ID")

class CourseCompleteResponse(BaseModel):
    """Schema for course completion response"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    completion_summary: Optional[Dict[str, Any]] = Field(None, description="Completion summary")

# User Authentication Schemas
class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    first_name: str = Field(..., min_length=1, max_length=100, description="User first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="User last name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "password": "securepassword123",
                "first_name": "John",
                "last_name": "Doe"
            }
        }

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "password": "securepassword123"
            }
        }

class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description="User first name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=100, description="User last name")
    email: Optional[EmailStr] = Field(None, description="User email address")
    
    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Smith",
                "email": "john.smith@example.com"
            }
        }

class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)"""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    first_name: str = Field(..., description="User first name")
    last_name: str = Field(..., description="User last name")
    is_active: bool = Field(..., description="Whether user account is active")
    is_verified: bool = Field(..., description="Whether user email is verified")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True

class UserProfileResponse(BaseModel):
    """Schema for user profile with statistics"""
    user_id: str = Field(..., description="User ID")
    total_chats: int = Field(..., description="Total number of chat interactions")
    quizzes_taken: int = Field(..., description="Total number of quizzes taken")
    day_streak: int = Field(..., description="Current day streak")
    days_active: int = Field(..., description="Total days active")
    last_activity_date: date = Field(..., description="Last activity date")
    streak_start_date: date = Field(..., description="Start date of current streak")
    created_at: datetime = Field(..., description="Profile creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    """Schema for updating user profile statistics"""
    total_chats: Optional[int] = Field(None, ge=0, description="Total number of chat interactions")
    quizzes_taken: Optional[int] = Field(None, ge=0, description="Total number of quizzes taken")
    day_streak: Optional[int] = Field(None, ge=0, description="Current day streak")
    days_active: Optional[int] = Field(None, ge=0, description="Total days active")

class AuthResponse(BaseModel):
    """Schema for authentication response"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="User information")
    profile: Optional[UserProfileResponse] = Field(None, description="User profile statistics")

class TokenRefresh(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str = Field(..., description="Refresh token")

class TokenRefreshResponse(BaseModel):
    """Schema for token refresh response"""
    access_token: str = Field(..., description="New JWT access token")
    refresh_token: str = Field(..., description="New refresh token")
    token_type: str = Field(default="bearer", description="Token type")

class LogoutRequest(BaseModel):
    """Schema for logout request"""
    refresh_token: str = Field(..., description="Refresh token to revoke")

class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "oldpassword123",
                "new_password": "newpassword456"
            }
        }

class PasswordReset(BaseModel):
    """Schema for password reset request"""
    email: EmailStr = Field(..., description="User email address")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john.doe@example.com"
            }
        }

class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "reset_token_here",
                "new_password": "newpassword456"
            }
        } 