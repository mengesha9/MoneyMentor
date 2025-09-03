from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import logging
from datetime import datetime
from supabase import Client
import json

from app.services.quiz_service import QuizService
from app.services.calculation_service import CalculationService
from app.services.content_service import ContentService
from app.core.database import get_supabase

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler with a higher log level
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(console_handler)

# Prevent the logger from propagating to the root logger
logger.propagate = False

# Define allowed session keys
ALLOWED_SESSION_KEYS = {
    "conversation_history",
    "quiz_context",
    "current_topic",
    "last_interaction",
    "user_preferences"
}

class QuizGeneratorTool(BaseTool):
    """Tool for generating educational quizzes based on context."""
    
    name: str = "Quiz Generator"
    description: str = "Generates educational quizzes based on the given context. Input: topic or concept to quiz about"
    
    class ArgsSchema(BaseModel):
        context: str = Field(..., description="Topic or concept to generate quiz about")
    
    quiz_service: QuizService = Field(default_factory=QuizService)
    
    async def _run(self, context: str) -> Dict[str, Any]:
        try:
            questions = await self.quiz_service.generate_quiz(context)
            return {
                "success": True,
                "questions": questions
            }
        except Exception as e:
            logger.error(f"Failed to generate quiz: {e}")
            return {
                "success": False,
                "error": str(e),
                "details": "Failed to generate quiz"
            }

class QuizLoggerTool(BaseTool):
    """Tool for logging quiz responses and updating user progress."""
    
    name: str = "Quiz Logger"
    description: str = "Logs quiz responses and updates user progress. Input: quiz_id and responses"
    
    class ArgsSchema(BaseModel):
        quiz_id: str = Field(..., description="ID of the quiz")
        responses: List[Dict[str, Any]] = Field(..., description="List of user responses")
    
    quiz_service: QuizService = Field(default_factory=QuizService)
    
    async def _run(self, quiz_id: str, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            success = await self.quiz_service.log_quiz_response(quiz_id, responses)
            return {
                "success": success,
                "quiz_id": quiz_id
            }
        except Exception as e:
            logger.error(f"Failed to log quiz responses: {e}")
            return {
                "success": False,
                "error": str(e),
                "details": "Failed to log quiz responses"
            }

class FinancialCalculatorTool(BaseTool):
    """Tool for calculating financial metrics"""
    
    name: str = "Financial Calculator"
    description: str = """Calculates financial metrics for debt payoff, savings goals, and loan amortization. 
    Supports three calculation types:
    1. credit_card_payoff - Calculate credit card payoff timeline
    2. savings_goal - Calculate monthly savings needed for a goal
    3. student_loan - Calculate loan amortization schedule
    
    Input: JSON with calculation_type and params. The tool will automatically extract parameters from natural language."""
    
    class ArgsSchema(BaseModel):
        calculation_type: str = Field(..., description="Type of calculation (credit_card_payoff, savings_goal, student_loan)")
        params: Dict[str, Any] = Field(..., description="Calculation parameters")
    
    calc_service: CalculationService = Field(default_factory=CalculationService)
    
    async def _run(self, calculation_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Debug logging
            logger.info(f"FinancialCalculatorTool: Received calculation_type={calculation_type}, params={params}")
            
            # Validate calculation type
            valid_types = ["credit_card_payoff", "savings_goal", "student_loan"]
            if calculation_type not in valid_types:
                return {
                    "success": False,
                    "error": f"Invalid calculation_type. Must be one of: {valid_types}",
                    "details": "Supported calculation types: credit_card_payoff, savings_goal, student_loan"
                }
            
            # Perform the calculation using the deterministic service
            result = await self.calc_service.calculate(calculation_type, params)
            
            # Ensure the result matches client requirements format
            if not isinstance(result, dict):
                return {
                    "success": False,
                    "error": "Invalid result format from calculation service",
                    "details": "Expected dictionary result with monthly_payment, months_to_payoff, total_interest, step_by_step_plan"
                }
            
            # Validate required fields are present
            required_fields = ["monthly_payment", "months_to_payoff", "total_interest", "step_by_step_plan"]
            missing_fields = [field for field in required_fields if field not in result]
            
            if missing_fields:
                return {
                    "success": False,
                    "error": f"Missing required fields in result: {missing_fields}",
                    "details": "Result must include monthly_payment, months_to_payoff, total_interest, step_by_step_plan"
                }
            
            # Return only the raw calculation result for LLM processing
            return {
                "success": True,
                "result": result,
                "calculation_type": calculation_type,
                "params_used": params,
                "monthly_payment": result.get('monthly_payment'),
                "months_to_payoff": result.get('months_to_payoff'),
                "total_interest": result.get('total_interest'),
                "step_by_step_plan": result.get('step_by_step_plan'),
                "total_amount": result.get('total_amount')
            }
            
        except Exception as e:
            logger.error(f"Failed to perform calculation: {e}")
            return {
                "success": False,
                "error": str(e),
                "details": "Failed to perform calculation. Please check your input parameters."
            }

class ContentRetrievalTool(BaseTool):
    """Tool for retrieving relevant educational content."""
    
    name: str = "Content Retriever"
    description: str = "Retrieves relevant educational content based on query. Input: search query and optional limit"
    
    class ArgsSchema(BaseModel):
        query: str = Field(
            ...,
            description="Search query",
            json_schema_extra={"example": "investment strategies"}
        )
        limit: int = Field(
            default=5,
            description="Maximum number of results to return",
            json_schema_extra={"minimum": 1, "maximum": 20}
        )
        
        model_config = {
            "extra": "allow",
            "validate_assignment": True
        }
    
    content_service: ContentService = Field(default_factory=ContentService)
    
    async def _run(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Run the content retrieval tool with robust error handling"""
        try:
            # Log the incoming query
            logger.info(f"ContentRetrievalTool: Received query - '{query}' with limit {limit}")
            
            if not query or not isinstance(query, str):
                logger.warning(f"ContentRetrievalTool: Invalid query received - '{query}'")
                return {
                    "success": False,
                    "error": "Invalid query parameter",
                    "details": "Query must be a non-empty string"
                }
            
            # Ensure limit is a positive integer
            try:
                limit = int(limit)
                if limit < 1:
                    logger.warning(f"ContentRetrievalTool: Invalid limit {limit}, defaulting to 5")
                    limit = 5
            except (ValueError, TypeError):
                logger.warning(f"ContentRetrievalTool: Invalid limit type {type(limit)}, defaulting to 5")
                limit = 5
            
            # Attempt to retrieve content
            logger.info(f"ContentRetrievalTool: Searching for content with query '{query}'")
            content = await self.content_service.search_content(query)
            
            # Limit results if needed
            if limit and isinstance(content, list):
                content = content[:limit]
                logger.info(f"ContentRetrievalTool: Found {len(content)} results, limited to {limit}")
            else:
                logger.info(f"ContentRetrievalTool: Found {len(content) if isinstance(content, list) else 0} results")
            
            return {
                "success": True,
                "content": content,
                "query_info": {
                    "query": query,
                    "limit": limit,
                    "result_count": len(content) if isinstance(content, list) else 0
                }
            }
            
        except Exception as e:
            logger.error(f"ContentRetrievalTool: Content retrieval failed for query '{query}': {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "details": "Failed to retrieve content",
                "query_info": {
                    "query": query,
                    "limit": limit,
                    "error_type": type(e).__name__
                }
            }

class SessionManagerTool(BaseTool):
    """Tool for managing user session data."""
    
    name: str = "Session Manager"
    description: str = "Manages user session data including conversation history and preferences"
    
    class ArgsSchema(BaseModel):
        action: str = Field(..., description="Action to perform (get/update)")
        data: Optional[Dict[str, Any]] = Field(None, description="Data to update")
    
    supabase: Client = Field(default_factory=get_supabase)
    
    async def _run(self, action: str, data: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        try:
            if not user_id:
                return {
                    "success": False,
                    "error": "User ID is required",
                    "details": "User ID must be provided for session management"
                }
                
            if action == "get":
                result = self.supabase.table('sessions').select('*').eq('user_id', user_id).execute()
                if not result.data:
                    return {
                        "success": True,
                        "data": {}
                    }
                return {
                    "success": True,
                    "data": result.data[0]['data'] if result.data else {}
                }
            elif action == "update" and data:
                # Filter allowed keys
                filtered_data = {k: v for k, v in data.items() if k in ALLOWED_SESSION_KEYS}
                current_data = await self._get_session(user_id)
                current_data.update(filtered_data)
                
                # Convert any UUID objects to strings in the data
                serialized_data = self._serialize_data(current_data)
                
                # Update in database
                self.supabase.table('sessions').upsert({
                    'user_id': user_id,
                    'data': serialized_data,
                    'updated_at': datetime.utcnow().isoformat()
                }).execute()
                
                return {
                    "success": True,
                    "data": serialized_data
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid action or missing data",
                    "details": "Action must be 'get' or 'update' with data"
                }
        except Exception as e:
            logger.error(f"Failed to manage session: {e}")
            return {
                "success": False,
                "error": str(e),
                "details": "Failed to manage session"
            }
    
    async def _get_session(self, user_id: str) -> Dict[str, Any]:
        result = self.supabase.table('sessions').select('*').eq('user_id', user_id).execute()
        if not result.data:
            return {}
        return result.data[0]['data'] if result.data else {}
    
    def _serialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert UUID objects to strings in the data dictionary"""
        serialized = {}
        for key, value in data.items():
            if isinstance(value, dict):
                serialized[key] = self._serialize_data(value)
            elif hasattr(value, 'hex'):  # Check if it's a UUID
                serialized[key] = str(value)
            else:
                serialized[key] = value
        return serialized

class ProgressTrackerTool(BaseTool):
    """Tool for tracking and analyzing user learning progress."""
    
    name: str = "Progress Tracker"
    description: str = "Tracks and analyzes user learning progress"
    
    class ArgsSchema(BaseModel):
        action: str = Field(..., description="Action to perform (get/update)")
        data: Optional[Dict[str, Any]] = Field(None, description="Progress data to update")
    
    supabase: Client = Field(default_factory=get_supabase)
    
    async def _run(self, action: str, data: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        try:
            if not user_id:
                return {
                    "success": False,
                    "error": "User ID is required",
                    "details": "User ID must be provided for progress tracking"
                }
                
            if action == "get":
                result = self.supabase.table('user_progress').select('*').eq('user_id', user_id).execute()
                return {
                    "success": True,
                    "data": result.data[0] if result.data else {}
                }
            elif action == "update" and data:
                # Update in database
                self.supabase.table('user_progress').upsert({
                    'user_id': user_id,
                    **data,
                    'updated_at': datetime.utcnow().isoformat()
                }).execute()
                
                return {
                    "success": True,
                    "data": data
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid action or missing data",
                    "details": "Action must be 'get' or 'update' with data"
                }
        except Exception as e:
            logger.error(f"Failed to track progress: {e}")
            return {
                "success": False,
                "error": str(e),
                "details": "Failed to track progress"
            } 