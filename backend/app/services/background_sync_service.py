import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta
from app.services.google_sheets_service import GoogleSheetsService
from app.services.supabase_listener_service import supabase_listener_service

logger = logging.getLogger(__name__)

class BackgroundSyncService:
    """Service for automatically syncing user profiles to Google Sheets"""
    
    def __init__(self):
        self.sheets_service = None  # Initialize lazily to avoid startup delays
        self.sync_interval = 300  # 5 minutes
        self.last_sync_time: Optional[datetime] = None
        self.is_running = False
        self.sync_task: Optional[asyncio.Task] = None
        self.notification_sync_delay = 30  # 30 seconds delay after notification
        self.sync_in_progress = False  # Prevent overlapping syncs
        self.sync_enabled = True  # Can be disabled if Google Sheets is having issues
        self.paused_for_requests = False  # Pause sync when there are active user requests
        self.sync_stats = {
            'total_syncs': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'last_sync_duration': 0
        }
    
    async def start_background_sync(self):
        """Start the background sync service"""
        if self.is_running:
            logger.warning("Background sync service is already running")
            return
        
        self.is_running = True
        logger.info("Starting background sync service for Google Sheets")
        
        # Initialize Google Sheets service lazily in background
        asyncio.create_task(self._initialize_sheets_service())
        
        # Start the background task
        self.sync_task = asyncio.create_task(self._sync_loop())
        
        logger.info("Background sync service started - will sync every 5 minutes")
    
    async def _initialize_sheets_service(self):
        """Initialize Google Sheets service in background to avoid startup delays"""
        try:
            logger.info("Initializing Google Sheets service in background...")
            self.sheets_service = GoogleSheetsService()
            logger.info("✅ Google Sheets service initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Sheets service: {e}")
            self.sheets_service = None
    
    async def stop_background_sync(self):
        """Stop the background sync service"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Stopping background sync service")
        
        # No external listeners to stop
        pass
        
        if self.sync_task:
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass
    
    async def _sync_loop(self):
        """Main sync loop that runs periodically with low priority"""
        while self.is_running:
            try:
                # Use asyncio.sleep(0) to yield control to other tasks
                await asyncio.sleep(0)
                
                # Skip sync if paused for user requests
                if self.paused_for_requests:
                    await asyncio.sleep(10)  # Check again in 10 seconds
                    continue
                
                # Perform sync with low priority
                await self._perform_sync()
                
                # Wait for the next sync interval
                await asyncio.sleep(self.sync_interval)
                
            except asyncio.CancelledError:
                logger.info("Background sync service cancelled")
                break
            except Exception as e:
                logger.error(f"Error in background sync loop: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(60)
    
    async def _perform_sync(self):
        """Perform the actual sync operation"""
        if self.sync_in_progress:
            logger.warning("Sync already in progress, skipping this cycle")
            return
        
        # Check if sync is enabled
        if not self.sync_enabled:
            logger.info("⏸️ Google Sheets sync is disabled, skipping sync")
            return
        
        # Check if Google Sheets service is initialized
        if self.sheets_service is None:
            logger.info("⏳ Google Sheets service not yet initialized, skipping sync")
            return
            
        self.sync_in_progress = True
        sync_start_time = datetime.utcnow()
        
        try:
            logger.info("🔄 Starting background sync to Google Sheets")
            self.sync_stats['total_syncs'] += 1
            
            # Yield control to other tasks
            await asyncio.sleep(0)
            
            # Update course statistics for all users and sync to Google Sheets
            try:
                from app.services.course_statistics_service import CourseStatisticsService
                from app.services.course_statistics_sync_service import course_statistics_sync_service
                stats_service = CourseStatisticsService()
                
                # Update course statistics in database
                stats_result = await stats_service.update_all_user_statistics()
                logger.info(f"Course statistics update: {stats_result['message']}")
                
                # Yield control to other tasks
                await asyncio.sleep(0)
                
                # Sync course statistics to Google Sheets (single source of truth)
                await course_statistics_sync_service.background_sync_all_users()
                logger.info("Course statistics synced to Google Sheets")
                
            except Exception as e:
                logger.warning(f"Failed to update course statistics: {e}")
            
            # Get all user profiles for export
            try:
                user_profiles = await self.sheets_service.get_all_user_profiles_for_export()
                
                if user_profiles:
                    # Export to Google Sheets with retry logic
                    max_retries = 3
                    success = False
                    
                    for attempt in range(max_retries):
                        try:
                            success = await self.sheets_service.export_user_profiles_to_sheet(user_profiles)
                            if success:
                                break
                        except Exception as e:
                            logger.warning(f"Google Sheets export attempt {attempt + 1} failed: {e}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(5)  # Wait 5 seconds before retry
                    
                    if success:
                        self.last_sync_time = datetime.utcnow()
                        self.sync_stats['successful_syncs'] += 1
                        sync_duration = (self.last_sync_time - sync_start_time).total_seconds()
                        self.sync_stats['last_sync_duration'] = sync_duration
                        logger.info(f"✅ Background sync successful: {len(user_profiles)} user profiles synced to Google Sheets in {sync_duration:.2f}s")
                    else:
                        self.sync_stats['failed_syncs'] += 1
                        logger.warning("⚠️ Background sync failed after retries - Google Sheets API may be temporarily unavailable")
                else:
                    logger.debug("No user profiles found for background sync")
                    
            except Exception as e:
                self.sync_stats['failed_syncs'] += 1
                logger.warning(f"⚠️ Could not fetch user profiles for sync: {e}")
                
        except Exception as e:
            self.sync_stats['failed_syncs'] += 1
            logger.error(f"❌ Error during background sync: {e}")
        finally:
            self.sync_in_progress = False
    
    # Removed complex notification callbacks - keeping it simple with just background polling
    
    async def force_sync_now(self):
        """Force an immediate sync (useful for testing or manual triggers)"""
        try:
            logger.info("Forcing immediate sync to Google Sheets")
            await self._perform_sync()
            return True
        except Exception as e:
            logger.error(f"Error during forced sync: {e}")
            return False
    
    def get_sync_status(self) -> dict:
        """Get current sync status and statistics"""
        return {
            'is_running': self.is_running,
            'sync_in_progress': self.sync_in_progress,
            'sync_enabled': self.sync_enabled,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'sync_interval_seconds': self.sync_interval,
            'next_sync_in_seconds': self._get_next_sync_in_seconds(),
            'statistics': self.sync_stats.copy()
        }
    
    def disable_sync(self):
        """Disable Google Sheets sync (useful when Google Sheets API is having issues)"""
        self.sync_enabled = False
        logger.info("⏸️ Google Sheets sync disabled")
    
    def enable_sync(self):
        """Enable Google Sheets sync"""
        self.sync_enabled = True
        logger.info("▶️ Google Sheets sync enabled")
    
    def pause_for_requests(self):
        """Pause sync when there are active user requests"""
        self.paused_for_requests = True
        logger.debug("⏸️ Background sync paused for user requests")
    
    def resume_after_requests(self):
        """Resume sync after user requests are complete"""
        self.paused_for_requests = False
        logger.debug("▶️ Background sync resumed after user requests")
    

    
    def _get_next_sync_in_seconds(self) -> Optional[int]:
        """Calculate seconds until next sync"""
        if not self.last_sync_time:
            return 0
        
        next_sync_time = self.last_sync_time + timedelta(seconds=self.sync_interval)
        now = datetime.utcnow()
        
        if next_sync_time > now:
            return int((next_sync_time - now).total_seconds())
        else:
            return 0

# Global instance
background_sync_service = BackgroundSyncService() 