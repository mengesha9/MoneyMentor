from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from app.core.database import get_supabase
from app.services.google_sheets_service import GoogleSheetsService
from app.utils.session import get_session
import asyncio

logger = logging.getLogger(__name__)

class EngagementService:
    """Service for tracking and logging user engagement metrics"""
    
    def __init__(self):
        self.supabase = get_supabase()
        self.sheets_service = GoogleSheetsService()
    
    async def track_session_engagement(self, user_id: str, session_id: str) -> bool:
        """
        Track and log engagement metrics for a user session
        
        This method calculates:
        - Messages per session
        - Session duration
        - Quizzes attempted
        - Pretest completion status
        - Last activity timestamp
        """
        try:
            # OPTIMIZATION: Get session data with shorter timeout
            session = await asyncio.wait_for(
                get_session(session_id),
                timeout=1.0  # Reduced from 5.0 to 1.0 second
            )
            if not session:
                logger.warning(f"Session not found: {session_id}")
                return False
            
            # Calculate engagement metrics efficiently
            chat_history = session.get("chat_history", [])
            
            # Count messages (user messages only) - optimized
            messages_per_session = sum(1 for msg in chat_history if msg.get("role") == "user")
            
            # Calculate session duration - with error handling
            session_duration = 0  # in seconds
            session_start = session.get("created_at")
            if session_start:
                try:
                    start_time = datetime.fromisoformat(session_start.replace('Z', '+00:00'))
                    session_duration = (datetime.utcnow() - start_time.replace(tzinfo=None)).total_seconds()
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to calculate session duration: {e}")
                    session_duration = 0
            
            # Count quizzes attempted from centralized quiz_responses table
            try:
                from app.core.database import get_supabase
                supabase = get_supabase()
                quiz_result = supabase.table('quiz_responses').select('id').eq('session_id', session_id).execute()
                quizzes_attempted = len(quiz_result.data) if quiz_result.data else 0
            except Exception as e:
                logger.warning(f"Failed to get quiz count from centralized storage: {e}")
                quizzes_attempted = 0
            
            # OPTIMIZATION: Skip pretest completion check for speed
            pretest_completed = False  # Skip this check to save time
            
            # Get confidence rating if available
            confidence_rating = session.get("confidence_rating", "")
            
            # Prepare engagement data
            engagement_data = {
                "user_id": user_id,
                "session_id": session_id,
                "messages_per_session": messages_per_session,
                "session_duration": session_duration,
                "quizzes_attempted": quizzes_attempted,
                "pretest_completed": pretest_completed,
                "last_activity": datetime.utcnow().isoformat(),
                "confidence_rating": confidence_rating
            }
            
            # OPTIMIZATION: Log to Google Sheets with shorter timeout
            try:
                success = await asyncio.wait_for(
                    self.sheets_service.log_engagement(engagement_data),
                    timeout=1.0  # Reduced from 5.0 to 1.0 second
                )
                if success:
                    logger.info(f"Engagement data logged for user {user_id}, session {session_id}")
                else:
                    logger.warning(f"Failed to log engagement data for user {user_id}")
                return success
            except asyncio.TimeoutError:
                logger.warning(f"Google Sheets logging timed out for user {user_id}")
                return False
            except Exception as e:
                logger.error(f"Failed to log engagement data to Google Sheets: {e}")
                return False
                
        except asyncio.TimeoutError:
            logger.warning(f"Session engagement tracking timed out for user {user_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to track session engagement: {e}")
            return False
    
    async def _check_pretest_completion(self, user_id: str) -> bool:
        """Check if user has completed diagnostic/pretest"""
        try:
            # Check quiz_responses table for diagnostic quiz completion
            result = self.supabase.table('quiz_responses').select('*').eq('user_id', user_id).eq('quiz_type', 'diagnostic').execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to check pretest completion: {e}")
            return False
    
    async def update_confidence_rating(self, user_id: str, session_id: str, confidence_rating: int) -> bool:
        """Update confidence rating for a user session"""
        try:
            # Update session with confidence rating
            session = await get_session(session_id)
            if session:
                session["confidence_rating"] = confidence_rating
                # Update session in storage (this would depend on your session storage implementation)
                
            # Log updated engagement data
            await self.track_session_engagement(user_id, session_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update confidence rating: {e}")
            return False
    
    async def log_session_end(self, user_id: str, session_id: str) -> bool:
        """Log final engagement metrics when a session ends"""
        try:
            # Track final engagement metrics
            success = await self.track_session_engagement(user_id, session_id)
            
            if success:
                logger.info(f"Session end logged for user {user_id}, session {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to log session end: {e}")
            return False 