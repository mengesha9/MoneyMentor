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
            
            # Use the manual sync service
            result = await manual_sync_service.sync_user_profiles_to_sheets(force_sync=True)
            
            if result['success']:
                self.last_sync_time = datetime.now()
                logger.info(f"✅ Triggered sync completed successfully - reason: {reason}")
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