"""
Manual Google Sheets Sync Service
This service provides on-demand sync without blocking startup or running continuously
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from app.services.google_sheets_service import GoogleSheetsService
from app.core.database import get_supabase
from app.config.sync_config import get_sync_interval, get_sync_setting

logger = logging.getLogger(__name__)

class ManualSyncService:
    """Service for manual/on-demand Google Sheets sync"""
    
    def __init__(self):
        self.sheets_service: Optional[GoogleSheetsService] = None
        self.sync_in_progress = False
        self.last_sync_time: Optional[datetime] = None
        self.sync_stats = {
            'total_syncs': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'last_sync_duration': 0,
            'last_sync_time': None
        }
    
    async def _get_sheets_service(self) -> GoogleSheetsService:
        """Lazy initialization of Google Sheets service"""
        if self.sheets_service is None:
            try:
                self.sheets_service = GoogleSheetsService()
                logger.info("✅ Google Sheets service initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Google Sheets service: {e}")
                raise
        return self.sheets_service
    
    async def sync_user_profiles_to_sheets(self, force_sync: bool = False) -> Dict[str, Any]:
        """
        Sync user profiles to Google Sheets on-demand
        
        Args:
            force_sync: If True, sync even if recently synced
            
        Returns:
            Dict with sync results and statistics
        """
        start_time = datetime.now()
        
        # Check if sync is already in progress
        if self.sync_in_progress:
            return {
                'success': False,
                'message': 'Sync already in progress',
                'duration': 0
            }
        
        # Check if we should skip sync (unless forced)
        if not force_sync and self.last_sync_time:
            time_since_last_sync = datetime.now() - self.last_sync_time
            cooldown_seconds = get_sync_interval('manual_sync_cooldown')
            if time_since_last_sync < timedelta(seconds=cooldown_seconds):
                return {
                    'success': True,
                    'message': f'Sync skipped - last sync was {time_since_last_sync.seconds} seconds ago',
                    'duration': 0,
                    'skipped': True
                }
        
        self.sync_in_progress = True
        self.sync_stats['total_syncs'] += 1
        
        try:
            logger.info("🔄 Starting manual Google Sheets sync...")
            
            # Get Google Sheets service
            sheets_service = await self._get_sheets_service()
            
            # Get user profiles from database
            supabase = get_supabase()
            result = supabase.table('user_profiles').select('*').execute()
            
            if not result.data:
                logger.info("No user profiles found to sync")
                return {
                    'success': True,
                    'message': 'No user profiles to sync',
                    'duration': (datetime.now() - start_time).total_seconds(),
                    'profiles_synced': 0
                }
            
            # Format profiles for Google Sheets export
            formatted_profiles = await sheets_service.get_all_user_profiles_for_export()
            
            if not formatted_profiles:
                logger.info("No formatted profiles to sync")
                return {
                    'success': True,
                    'message': 'No profiles to sync',
                    'duration': (datetime.now() - start_time).total_seconds(),
                    'profiles_synced': 0
                }
            
            # Sync to Google Sheets (note: singular method name)
            success = await sheets_service.export_user_profiles_to_sheet(formatted_profiles)
            
            # Update stats
            self.last_sync_time = datetime.now()
            if success:
                self.sync_stats['successful_syncs'] += 1
                success_count = len(formatted_profiles)
            else:
                self.sync_stats['failed_syncs'] += 1
                success_count = 0
                
            self.sync_stats['last_sync_duration'] = (datetime.now() - start_time).total_seconds()
            self.sync_stats['last_sync_time'] = self.last_sync_time.isoformat()
            
            logger.info(f"✅ Manual sync completed: {success_count} profiles synced")
            
            return {
                'success': success,
                'message': f'Successfully synced {success_count} profiles' if success else 'Sync failed',
                'duration': (datetime.now() - start_time).total_seconds(),
                'profiles_synced': success_count,
                'total_profiles': len(formatted_profiles)
            }
            
        except Exception as e:
            self.sync_stats['failed_syncs'] += 1
            logger.error(f"❌ Manual sync failed: {e}")
            return {
                'success': False,
                'message': f'Sync failed: {str(e)}',
                'duration': (datetime.now() - start_time).total_seconds(),
                'error': str(e)
            }
        finally:
            self.sync_in_progress = False
    
    async def sync_single_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Sync a single user profile to Google Sheets"""
        start_time = datetime.now()
        
        try:
            logger.info(f"🔄 Syncing single user profile: {user_id}")
            
            # Get Google Sheets service
            sheets_service = await self._get_sheets_service()
            
            # Get specific user profile
            supabase = get_supabase()
            result = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
            
            if not result.data:
                return {
                    'success': False,
                    'message': f'User profile not found for user {user_id}',
                    'duration': (datetime.now() - start_time).total_seconds()
                }
            
            # Sync to Google Sheets
            success_count = await sheets_service.export_user_profiles_to_sheets(result.data)
            
            logger.info(f"✅ Single user sync completed: {user_id}")
            
            return {
                'success': True,
                'message': f'Successfully synced user {user_id}',
                'duration': (datetime.now() - start_time).total_seconds(),
                'user_id': user_id
            }
            
        except Exception as e:
            logger.error(f"❌ Single user sync failed for {user_id}: {e}")
            return {
                'success': False,
                'message': f'Sync failed for user {user_id}: {str(e)}',
                'duration': (datetime.now() - start_time).total_seconds(),
                'error': str(e)
            }
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status and statistics"""
        return {
            'sync_in_progress': self.sync_in_progress,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'stats': self.sync_stats.copy()
        }
    
    def is_sync_available(self) -> bool:
        """Check if sync is available (not in progress and not too recent)"""
        if self.sync_in_progress:
            return False
        
        if self.last_sync_time:
            time_since_last_sync = datetime.now() - self.last_sync_time
            return time_since_last_sync >= timedelta(minutes=2)
        
        return True
    
    async def sync_specific_user_profiles_to_sheets(self, user_ids: List[str], force_sync: bool = False) -> Dict[str, Any]:
        """
        Sync specific user profiles to Google Sheets
        
        Args:
            user_ids: List of user IDs to sync
            force_sync: Whether to force sync regardless of cooldown
        
        Returns:
            Dict with sync results and statistics
        """
        start_time = datetime.now()
        
        if not user_ids:
            return {
                'success': True,
                'message': 'No user IDs provided',
                'duration': 0,
                'profiles_synced': 0
            }
        
        try:
            logger.info(f"🔄 Starting targeted sync for {len(user_ids)} users...")
            
            # Get Google Sheets service
            sheets_service = await self._get_sheets_service()
            
            # Get specific user profiles from database
            supabase = get_supabase()
            result = supabase.table('user_profiles').select('*').in_('user_id', user_ids).execute()
            
            if not result.data:
                logger.info(f"No user profiles found for user IDs: {user_ids}")
                return {
                    'success': True,
                    'message': f'No profiles found for user IDs: {user_ids}',
                    'duration': (datetime.now() - start_time).total_seconds(),
                    'profiles_synced': 0
                }
            
            # Format profiles for export (same as full sync)
            formatted_profiles = []
            for profile in result.data:
                user_id = profile['user_id']
                
                try:
                    # Get user information
                    user_result = supabase.table('users').select(
                        'first_name, last_name, email'
                    ).eq('id', user_id).single().execute()
                    
                    if user_result.data:
                        user_info = user_result.data
                        # Process course statistics
                        course_stats = profile.get('course_statistics', [])
                        course_summary = self._format_course_statistics(course_stats)
                        
                        formatted_profiles.append({
                            'user_id': user_id,
                            'first_name': user_info.get('first_name', ''),
                            'last_name': user_info.get('last_name', ''),
                            'email': user_info.get('email', ''),
                            'total_chats': profile.get('total_chats', 0),
                            'quizzes_taken': profile.get('quizzes_taken', 0),
                            'day_streak': profile.get('day_streak', 0),
                            'days_active': profile.get('days_active', 0),
                            'courses_enrolled': course_summary['courses_enrolled'],
                            'total_course_score': course_summary['total_score'],
                            'courses_completed': course_summary['courses_completed'],
                            'course_details': course_summary['course_details']
                        })
                except Exception as user_error:
                    logger.warning(f"Could not get user details for {user_id}: {user_error}")
            
            if not formatted_profiles:
                return {
                    'success': True,
                    'message': 'No profiles could be formatted for sync',
                    'duration': (datetime.now() - start_time).total_seconds(),
                    'profiles_synced': 0
                }
            
            # Sync to Google Sheets using the existing export method
            success = await sheets_service.export_user_profiles_to_sheet(formatted_profiles)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            if success:
                logger.info(f"✅ Targeted sync completed successfully for {len(formatted_profiles)} profiles in {duration:.2f}s")
                return {
                    'success': True,
                    'message': f'Successfully synced {len(formatted_profiles)} user profiles',
                    'duration': duration,
                    'profiles_synced': len(formatted_profiles)
                }
            else:
                logger.warning(f"⚠️ Targeted sync failed for {len(user_ids)} users")
                return {
                    'success': False,
                    'message': 'Failed to sync user profiles to Google Sheets',
                    'duration': duration,
                    'profiles_synced': 0
                }
                
        except Exception as e:
            logger.error(f"❌ Targeted sync error: {e}")
            return {
                'success': False,
                'message': f'Sync failed: {str(e)}',
                'duration': (datetime.now() - start_time).total_seconds(),
                'profiles_synced': 0
            }
    
    def _format_course_statistics(self, course_stats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format course statistics for Google Sheets export
        
        Args:
            course_stats: List of course statistics objects
        
        Returns:
            Dictionary with formatted course statistics
        """
        if not course_stats:
            return {
                'courses_enrolled': 0,
                'total_score': 0,
                'courses_completed': 0,
                'course_details': ''
            }
        
        courses_enrolled = len(course_stats)
        total_score = sum(stat.get('score', 0) for stat in course_stats)
        courses_completed = sum(1 for stat in course_stats if stat.get('tabs_completed', 0) > 0)
        
        # Format course details as a readable string
        course_details = []
        for stat in course_stats:
            course_name = stat.get('course_name', 'Unknown')
            score = stat.get('score', 0)
            tabs_completed = stat.get('tabs_completed', 0)
            level = stat.get('level', 'easy')
            questions_taken = stat.get('total_questions_taken', 0)
            
            detail = f"{course_name}: {score}% ({tabs_completed} tabs, {questions_taken} questions, {level})"
            course_details.append(detail)
        
        return {
            'courses_enrolled': courses_enrolled,
            'total_score': total_score,
            'courses_completed': courses_completed,
            'course_details': ' | '.join(course_details)
        }

# Global instance
manual_sync_service = ManualSyncService()