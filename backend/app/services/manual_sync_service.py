"""
Manual Google Sheets Sync Service
This service provides on-demand sync without blocking startup or running continuously
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
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
            
            # Sync to Google Sheets
            success_count = await sheets_service.export_user_profiles_to_sheets(result.data)
            
            # Update stats
            self.last_sync_time = datetime.now()
            self.sync_stats['successful_syncs'] += 1
            self.sync_stats['last_sync_duration'] = (datetime.now() - start_time).total_seconds()
            self.sync_stats['last_sync_time'] = self.last_sync_time.isoformat()
            
            logger.info(f"✅ Manual sync completed: {success_count}/{len(result.data)} profiles synced")
            
            return {
                'success': True,
                'message': f'Successfully synced {success_count} profiles',
                'duration': (datetime.now() - start_time).total_seconds(),
                'profiles_synced': success_count,
                'total_profiles': len(result.data)
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

# Global instance
manual_sync_service = ManualSyncService()