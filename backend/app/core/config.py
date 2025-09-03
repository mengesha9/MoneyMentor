from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os
from typing import List, Optional
from pathlib import Path

# Get the project root directory
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file
load_dotenv(dotenv_path=ROOT_DIR / ".env", override=True)

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "MoneyMentor"
    
    # OpenAI Configuration
    OPENAI_API_KEY: str
    OPENAI_MODEL_GPT4: str = "gpt-4"
    OPENAI_MODEL_GPT4_MINI: str = "gpt-3.5-turbo"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: Optional[str] = None
    
    # Authentication Configuration
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 60 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days
    
    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379"
    
    # Google Sheets Configuration
    GOOGLE_SHEETS_CREDENTIALS: Optional[dict] = None
    GOOGLE_SHEETS_SPREADSHEET_ID: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    GOOGLE_CLIENT_EMAIL: Optional[str] = None
    GOOGLE_PRIVATE_KEY: Optional[str] = None
    GOOGLE_SHEET_ID: Optional[str] = None
    
    # Application Settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:8000", "https://frontend-new-647308514289.us-central1.run.app"]
    
    # Webhook Configuration
    WEBHOOK_URL: str = ""
    MAKE_WEBHOOK_URL: str = ""
    QUIZ_WEBHOOK_URL: str = ""
    CALCULATION_WEBHOOK_URL: str = ""
    
    # Calculation Service
    CALC_SERVICE_URL: str = ""
    
    # Quiz Configuration
    QUIZ_FREQUENCY: int = 3  # Number of chat turns between quizzes
    MIN_QUIZ_QUESTIONS: int = 3
    MAX_QUIZ_QUESTIONS: int = 5
    
    # Content Processing
    UPLOAD_DIR: str = "uploads"
    MAX_CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    SUPPORTED_FILE_TYPES: list = ["pdf", "pptx", "docx", "txt"]
    
    # Vector Store Settings
    VECTOR_STORE_INDEX_NAME: str = "content_chunks"
    VECTOR_STORE_DIMENSION: int = 1536  # OpenAI embedding dimension
    VECTOR_STORE_METRIC: str = "cosine"
    
    # Quiz Trigger Interval
    QUIZ_TRIGGER_INTERVAL: int = 3
    
    class Config:
        env_file = str(ROOT_DIR / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"  # Allow extra fields in .env file

# Create settings instance
settings = Settings() 