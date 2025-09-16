from typing import Dict, Any, Optional, List
from datetime import datetime, date, timedelta
import logging
from app.core.database import get_supabase
from app.core.auth import get_user_by_id, update_user, delete_user, change_user_password
from app.models.schemas import UserProfileResponse, UserProfileUpdate
from app.services.triggered_sync_service import triggered_sync_service
import asyncio
from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)

class UserService:
    """Service for managing user profiles and statistics"""
    
    def __init__(self):
        self.supabase = get_supabase()
    
    async def get_user_profile(self, user_id: str, background_tasks: Optional[BackgroundTasks] = None) -> Optional[UserProfileResponse]:
        """Get user profile with statistics"""
        try:
            result = await asyncio.to_thread(
                lambda: self.supabase.table('user_profiles').select('*').eq('user_id', user_id).single().execute()
            )
            
            if result.data:
                return UserProfileResponse(**result.data)
            
            # If no profile exists, create one
            logger.info(f"Creating profile for user {user_id}")
            return await self.create_user_profile(user_id, background_tasks)
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            # Try to create profile even if query failed
            try:
                logger.info(f"Attempting to create profile for user {user_id} after error")
                return await self.create_user_profile(user_id, background_tasks)
            except Exception as create_error:
                logger.error(f"Failed to create profile for user {user_id}: {create_error}")
                return None
    
    async def create_user_profile(self, user_id: str, background_tasks: Optional[BackgroundTasks] = None) -> Optional[UserProfileResponse]:
        """Create a new user profile"""
        try:
            profile_data = {
                'user_id': user_id,
                'total_chats': 0,
                'quizzes_taken': 0,
                'day_streak': 0,
                'days_active': 0,
                'last_activity_date': date.today().isoformat(),
                'streak_start_date': date.today().isoformat()
            }
            
            result = await asyncio.to_thread(
                lambda: self.supabase.table('user_profiles').insert(profile_data).execute()
            )
            
            if result.data:
                # Trigger sync to Google Sheets asynchronously in background
                if background_tasks:
                    background_tasks.add_task(triggered_sync_service.trigger_sync_background, f"user_profile_created_{user_id}")
                    logger.info(f"User profile created for {user_id} - background sync scheduled")
                else:
                    # Fallback to synchronous call if no background tasks provided
                    triggered_sync_service.trigger_sync(f"user_profile_created_{user_id}")
                    logger.info(f"User profile created for {user_id} - sync triggered synchronously")
                return UserProfileResponse(**result.data[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
            return None
    
    async def update_user_profile(self, user_id: str, profile_data: UserProfileUpdate, background_tasks: Optional[BackgroundTasks] = None) -> Optional[UserProfileResponse]:
        """Update user profile statistics"""
        try:
            # Convert Pydantic model to dict, excluding None values
            update_data = {k: v for k, v in profile_data.dict().items() if v is not None}
            
            if not update_data:
                return await self.get_user_profile(user_id)
            
            # Add updated_at timestamp
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            result = await asyncio.to_thread(
                lambda: self.supabase.table('user_profiles').update(update_data).eq('user_id', user_id).execute()
            )
            
            if result.data:
                # Trigger sync to Google Sheets asynchronously in background
                if background_tasks:
                    background_tasks.add_task(triggered_sync_service.trigger_sync_background, f"user_profile_updated_{user_id}")
                    logger.debug(f"User profile updated for {user_id} - background sync scheduled")
                else:
                    # Fallback to synchronous call if no background tasks provided
                    triggered_sync_service.trigger_sync(f"user_profile_updated_{user_id}")
                    logger.debug(f"User profile updated for {user_id} - sync triggered synchronously")
                return UserProfileResponse(**result.data[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return None
    
    async def increment_chat_count(self, user_id: str) -> bool:
        """Increment user's chat count"""
        try:
            # Get current profile
            profile = await self.get_user_profile(user_id)
            if not profile:
                return False
            
            # Increment chat count
            new_count = profile.total_chats + 1
            update_data = UserProfileUpdate(total_chats=new_count)
            
            updated_profile = await self.update_user_profile(user_id, update_data)
            return updated_profile is not None
            
        except Exception as e:
            logger.error(f"Error incrementing chat count: {e}")
            return False
    
    async def increment_quiz_count(self, user_id: str) -> bool:
        """Increment user's quiz count"""
        try:
            # Get current profile
            profile = await self.get_user_profile(user_id)
            if not profile:
                return False
            
            # Increment quiz count
            new_count = profile.quizzes_taken + 1
            update_data = UserProfileUpdate(quizzes_taken=new_count)
            
            updated_profile = await self.update_user_profile(user_id, update_data)
            return updated_profile is not None
            
        except Exception as e:
            logger.error(f"Error incrementing quiz count: {e}")
            return False
    
    # REMOVED: _sync_user_profiles_to_sheets() and _background_sync_to_sheets()
    # Google Sheets sync is now handled exclusively by BackgroundSyncService
    # which runs every 5 minutes and doesn't block user operations

    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        try:
            # Get user profile
            profile = await self.get_user_profile(user_id)
            if not profile:
                return {}
            
            # Get additional statistics from user_sessions and centralized quiz_responses
            chat_result = await asyncio.to_thread(
                lambda: self.supabase.table('user_sessions').select('chat_history').eq('user_id', str(user_id)).execute()
            )
            
            # Count total chat messages from user_sessions
            total_chat_messages = 0
            for session in chat_result.data:
                chat_history = session.get('chat_history', [])
                total_chat_messages += len(chat_history)
            
            # Get quiz statistics from centralized quiz_responses table
            quiz_responses = await asyncio.to_thread(
                lambda: self.supabase.table('quiz_responses').select('correct, quiz_type').eq('user_id', str(user_id)).execute()
            )
            total_quiz_responses = len(quiz_responses.data) if quiz_responses.data else 0
            
            # Calculate accuracy from quiz responses
            correct_answers = 0
            total_answers = 0
            
            for response in quiz_responses.data:
                total_answers += 1
                if response.get('correct', False):
                    correct_answers += 1
            
            accuracy = (correct_answers / total_answers * 100) if total_answers > 0 else 0
            
            return {
                'profile': profile.dict(),
                'statistics': {
                    'total_chat_messages': total_chat_messages,
                    'total_quiz_responses': total_quiz_responses,
                    'quiz_accuracy': round(accuracy, 2),
                    'correct_answers': correct_answers,
                    'total_answers': total_answers
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return {}
    
    async def get_user_activity_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user activity summary for the last N days"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get chat activity from user_sessions
            chat_result = await asyncio.to_thread(
                lambda: self.supabase.table('user_sessions').select('chat_history, created_at, updated_at').eq('user_id', str(user_id)).gte('created_at', start_date.isoformat()).execute()
            )
            
            # Get quiz activity
            quiz_result = await asyncio.to_thread(
                lambda: self.supabase.table('quiz_responses').select('created_at, correct').eq('user_id', str(user_id)).gte('created_at', start_date.isoformat()).execute()
            )
            
            # Process activity by day
            activity_by_day = {}
            for i in range(days):
                day = (end_date - timedelta(days=i)).date()
                activity_by_day[day.isoformat()] = {
                    'chats': 0,
                    'quizzes': 0,
                    'correct_answers': 0,
                    'total_answers': 0
                }
            
            # Count chat activity from user_sessions
            for session in chat_result.data:
                chat_history = session.get('chat_history', [])
                # Count messages in this session
                message_count = len(chat_history)
                if message_count > 0:
                    # Use session creation date for activity tracking
                    session_date = datetime.fromisoformat(session['created_at'].replace('Z', '+00:00')).date()
                    if session_date.isoformat() in activity_by_day:
                        activity_by_day[session_date.isoformat()]['chats'] += message_count
            
            # Count quiz activity
            for quiz in quiz_result.data:
                quiz_date = datetime.fromisoformat(quiz['created_at'].replace('Z', '+00:00')).date()
                if quiz_date.isoformat() in activity_by_day:
                    activity_by_day[quiz_date.isoformat()]['quizzes'] += 1
                    activity_by_day[quiz_date.isoformat()]['total_answers'] += 1
                    if quiz.get('correct', False):
                        activity_by_day[quiz_date.isoformat()]['correct_answers'] += 1
            
            return {
                'period_days': days,
                'start_date': start_date.date().isoformat(),
                'end_date': end_date.date().isoformat(),
                'activity_by_day': activity_by_day
            }
            
        except Exception as e:
            logger.error(f"Error getting user activity summary: {e}")
            return {}
    
    async def delete_user_account(self, user_id: str, password: str) -> bool:
        """Delete user account and all associated data"""
        try:
            # Verify password before deletion
            if not await change_user_password(user_id, password, password):  # This will verify the password
                return False
            
            # Delete user (this will cascade to user_profiles due to foreign key)
            success = await delete_user(user_id)
            
            if success:
                # REMOVED: Google Sheets sync - handled by BackgroundSyncService
                # The background service will handle the deletion sync in the next cycle
                logger.info(f"User account {user_id} deleted successfully - will be synced to Google Sheets by background service")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting user account: {e}")
            return False
    
    async def get_leaderboard_data(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard data for top users"""
        try:
            # Get users with highest day streaks
            result = await asyncio.to_thread(
                lambda: self.supabase.table('user_profiles').select(
                    'user_id, day_streak, days_active, total_chats, quizzes_taken'
                ).order('day_streak', desc=True).limit(limit).execute()
            )
            
            if not result.data:
                return []
            
            # Get all user IDs for bulk query (FIXING N+1 PROBLEM)
            user_ids = [profile['user_id'] for profile in result.data]
            
            # Single bulk query instead of individual queries per user
            users_result = await asyncio.to_thread(
                lambda: self.supabase.table('users').select('id, first_name, last_name').in_('id', user_ids).execute()
            )
            
            # Create lookup dictionary for fast access
            users_dict = {user['id']: user for user in users_result.data} if users_result.data else {}
            
            leaderboard = []
            for i, profile in enumerate(result.data):
                user_info = users_dict.get(profile['user_id'], {})
                
                leaderboard.append({
                    'rank': i + 1,
                    'user_id': profile['user_id'],
                    'name': f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip(),
                    'day_streak': profile['day_streak'],
                    'days_active': profile['days_active'],
                    'total_chats': profile['total_chats'],
                    'quizzes_taken': profile['quizzes_taken']
                })
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting leaderboard data: {e}")
            return [] 