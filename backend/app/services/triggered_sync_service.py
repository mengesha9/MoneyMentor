"""
Triggered Google Sheets Sync Service
This service syncs to Google Sheets when specific user actions occur
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.services.manual_sync_service import manual_sync_service
from app.config.sync_config import get_sync_interval, get_sync_setting

logger = logging.getLogger(__name__)

class TriggeredSyncService:
    """Service for syncing to Google Sheets when user actions trigger it"""
    
    def __init__(self):
        self.sync_cooldown = get_sync_interval('triggered_sync_cooldown')  # Configurable cooldown
        self.last_sync_time: Optional[datetime] = None
        self.pending_sync = False
        self.sync_task: Optional[asyncio.Task] = None
        self.enabled = get_sync_setting('enable_triggered_sync')
    
    @property
    def pending(self) -> bool:
        """Backward compatibility property for pending_sync"""
        return self.pending_sync
    
    def trigger_sync(self, reason: str = "user_action") -> bool:
        """
        Trigger a sync to Google Sheets
        
        Args:
            reason: Reason for the sync trigger
            
        Returns:
            True if sync was triggered, False if skipped due to cooldown or disabled
        """
        # Check if triggered sync is enabled
        if not self.enabled:
            logger.debug(f"⏳ Triggered sync disabled - reason: {reason}")
            return False
        
        now = datetime.now()
        
        # Check cooldown
        if self.last_sync_time:
            time_since_last_sync = now - self.last_sync_time
            if time_since_last_sync < timedelta(seconds=self.sync_cooldown):
                logger.info(f"⏳ Sync skipped due to cooldown ({time_since_last_sync.seconds}s ago) - reason: {reason}")
                return False
        
        # Check if sync is already pending
        if self.pending_sync:
            logger.info(f"⏳ Sync already pending - reason: {reason}")
            return False
        
        # Trigger sync
        self.pending_sync = True
        logger.info(f"🔄 Triggering sync - reason: {reason}")
        
        # Start sync task
        self.sync_task = asyncio.create_task(self._perform_triggered_sync(reason))
        
        return True
    
    async def _perform_triggered_sync(self, reason: str):
        """Perform the actual sync operation"""
        try:
            logger.info(f"🔄 Starting triggered sync - reason: {reason}")
            
            # Check if this is a user-specific sync
            user_id = None
            if reason.startswith("user_profile_created_"):
                user_id = reason.replace("user_profile_created_", "")
            elif reason.startswith("user_profile_updated_"):
                user_id = reason.replace("user_profile_updated_", "")
            
            if user_id:
                # Use targeted sync for specific user
                logger.info(f"🎯 Using targeted sync for user {user_id}")
                result = await manual_sync_service.sync_specific_user_profiles_to_sheets([user_id], force_sync=True)
            else:
                # Use full sync for other reasons
                logger.info(f"🔄 Using full sync - reason: {reason}")
                result = await manual_sync_service.sync_user_profiles_to_sheets(force_sync=True)
            
            if result['success']:
                self.last_sync_time = datetime.now()
                profiles_synced = result.get('profiles_synced', 0)
                logger.info(f"✅ Triggered sync completed successfully - reason: {reason}, profiles: {profiles_synced}")
            else:
                logger.warning(f"⚠️ Triggered sync failed - reason: {reason}, error: {result.get('message', 'Unknown error')}")
            
        except Exception as e:
            logger.error(f"❌ Triggered sync error - reason: {reason}, error: {e}")
        finally:
            self.pending_sync = False
            self.sync_task = None
    
    def set_sync_cooldown(self, seconds: int):
        """Set the cooldown period between syncs"""
        self.sync_cooldown = seconds
        logger.info(f"⏰ Sync cooldown set to {seconds} seconds")
    
    def trigger_sync_background(self, reason: str = "user_action") -> None:
        """
        Trigger sync for use in FastAPI background tasks
        This creates a new event loop if needed and runs the async sync
        """
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, create a task
                loop.create_task(self._perform_triggered_sync_safe(reason))
            else:
                # If no loop is running, run in new loop
                asyncio.run(self._perform_triggered_sync_safe(reason))
        except RuntimeError:
            # No event loop exists, create a new one
            asyncio.run(self._perform_triggered_sync_safe(reason))
    
    async def _perform_triggered_sync_safe(self, reason: str):
        """Safe wrapper for performing sync that handles all edge cases"""
        try:
            if not self.enabled:
                logger.info(f"🚫 Sync disabled - skipping sync for reason: {reason}")
                return
            
            if self.is_in_cooldown():
                logger.info(f"⏰ Sync in cooldown period - skipping sync for reason: {reason}")
                return
            
            if self.pending_sync:
                logger.info(f"⏳ Sync already pending - reason: {reason}")
                return
            
            # Set pending state
            self.pending_sync = True
            logger.info(f"🔄 Starting background sync - reason: {reason}")
            
            # Check if this is a user-specific sync
            user_id = None
            if reason.startswith("user_profile_created_"):
                user_id = reason.replace("user_profile_created_", "")
            elif reason.startswith("user_profile_updated_"):
                user_id = reason.replace("user_profile_updated_", "")
            
            if user_id:
                # Use FULL sync even for specific user to preserve existing data
                # This ensures all users remain in the sheet when new ones register
                logger.info(f"� Using full sync to preserve existing users (triggered by user {user_id})")
                result = await manual_sync_service.sync_user_profiles_to_sheets(force_sync=True)
            else:
                # Use full sync for other reasons
                logger.info(f"🌍 Using full sync for reason: {reason}")
                result = await manual_sync_service.sync_user_profiles_to_sheets()
            
            if result.get('success'):
                logger.info(f"✅ Background sync completed successfully - {result.get('message', 'No details')}")
                self.last_sync_time = datetime.now()
            else:
                logger.error(f"❌ Background sync failed - {result.get('error', 'Unknown error')}")
            
        except Exception as e:
            logger.error(f"❌ Background sync exception: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Always clear pending state
            self.pending_sync = False
    
    def is_in_cooldown(self) -> bool:
        """Check if sync is in cooldown period"""
        if not self.last_sync_time:
            return False
        
        time_since_last = (datetime.now() - self.last_sync_time).total_seconds()
        return time_since_last < self.sync_cooldown
    
    def get_cooldown_remaining(self) -> int:
        """Get remaining cooldown time in seconds"""
        if not self.last_sync_time:
            return 0
        
        time_since_last = (datetime.now() - self.last_sync_time).total_seconds()
        remaining = self.sync_cooldown - time_since_last
        return max(0, int(remaining))
    
    def set_sync_cooldown(self, seconds: int):
        """Set sync cooldown period"""
        self.sync_cooldown = seconds
        logger.info(f"⏰ Sync cooldown set to {seconds} seconds")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status"""
        return {
            'pending_sync': self.pending_sync,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'sync_cooldown_seconds': self.sync_cooldown,
            'time_since_last_sync': (datetime.now() - self.last_sync_time).total_seconds() if self.last_sync_time else None
        }

# Global instance
triggered_sync_service = TriggeredSyncService()