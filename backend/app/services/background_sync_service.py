import asyncio
import logging
import os
import threading
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from app.services.google_sheets_service import GoogleSheetsService
from app.services.supabase_listener_service import supabase_listener_service

logger = logging.getLogger(__name__)

@dataclass
class SyncConfig:
    """Configuration for background sync service"""
    interval_seconds: int = int(os.getenv('SYNC_INTERVAL_SECONDS', '1800'))  # 30 minutes default
    max_retries: int = int(os.getenv('SYNC_MAX_RETRIES', '3'))
    retry_delay_seconds: int = int(os.getenv('SYNC_RETRY_DELAY_SECONDS', '5'))
    enable_course_stats: bool = os.getenv('SYNC_ENABLE_COURSE_STATS', 'true').lower() == 'true'
    enable_user_profiles: bool = os.getenv('SYNC_ENABLE_USER_PROFILES', 'true').lower() == 'true'
    enable_incremental_sync: bool = os.getenv('SYNC_ENABLE_INCREMENTAL', 'true').lower() == 'true'
    enable_quiz_responses: bool = os.getenv('SYNC_ENABLE_QUIZ_RESPONSES', 'true').lower() == 'true'
    enable_engagement_logs: bool = os.getenv('SYNC_ENABLE_ENGAGEMENT_LOGS', 'true').lower() == 'true'
    enable_chat_logs: bool = os.getenv('SYNC_ENABLE_CHAT_LOGS', 'true').lower() == 'true'
    enable_course_progress: bool = os.getenv('SYNC_ENABLE_COURSE_PROGRESS', 'true').lower() == 'true'
    health_check_interval: int = int(os.getenv('SYNC_HEALTH_CHECK_INTERVAL', '60'))  # 1 minute
    max_consecutive_failures: int = int(os.getenv('SYNC_MAX_CONSECUTIVE_FAILURES', '5'))
    sync_delay_seconds: int = int(os.getenv('SYNC_DELAY_SECONDS', '10'))  # Delay between sync operations

class BackgroundSyncService:
    """Enhanced service for automatically syncing user profiles to Google Sheets
    
    Features:
    - Non-blocking background operation
    - Configurable sync intervals
    - Comprehensive error handling and recovery
    - Health monitoring and metrics
    - Graceful shutdown
    - Automatic retry logic
    """
    
    def __init__(self, config: Optional[SyncConfig] = None):
        self.config = config or SyncConfig()
        self.sheets_service = None  # Initialize lazily to avoid startup delays
        self.comprehensive_sync_service = None  # Initialize comprehensive sync service
        self.last_sync_time: Optional[datetime] = None
        self.is_running = False
        self.sync_task: Optional[asyncio.Task] = None
        self.health_check_task: Optional[asyncio.Task] = None
        self.notification_sync_delay = 30  # 30 seconds delay after notification
        self.sync_in_progress = False  # Prevent overlapping syncs
        self.sync_enabled = True  # Can be disabled if Google Sheets is having issues
        self.paused_for_requests = False  # Pause sync when there are active user requests
        self.consecutive_failures = 0
        self.last_health_check: Optional[datetime] = None

        # Enhanced statistics
        self.sync_stats = {
            'total_syncs': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'last_sync_duration': 0,
            'average_sync_duration': 0,
            'total_sync_duration': 0,
            'last_error': None,
            'last_error_time': None,
            'health_status': 'unknown',
            'uptime_seconds': 0,
            'start_time': None
        }
    
    async def start_background_sync(self):
        """Start the background sync service with enhanced monitoring"""
        if self.is_running:
            logger.warning("Background sync service is already running")
            return
        
        self.is_running = True
        self.sync_stats['start_time'] = datetime.utcnow()
        self.sync_stats['health_status'] = 'starting'
        logger.info("🚀 Starting enhanced background sync service...")
        logger.info(f"📊 Sync interval: {self.config.interval_seconds} seconds ({self.config.interval_seconds // 60} minutes)")
        logger.info(f"⏳ Sync delay between operations: {self.config.sync_delay_seconds} seconds")
        logger.info(f"🔄 Max retries: {self.config.max_retries}")
        logger.info(f"🏥 Health check interval: {self.config.health_check_interval} seconds")
        
        # Initialize Google Sheets service lazily in background
        asyncio.create_task(self._initialize_sheets_service())
        
        # Start the main sync loop
        self.sync_task = asyncio.create_task(self._sync_loop())
        
        # Start health monitoring
        self.health_check_task = asyncio.create_task(self._health_monitor_loop())
        
        logger.info("✅ Enhanced background sync service started successfully")
        logger.info(f"⏰ Next sync in {self.config.interval_seconds} seconds")
    
    async def _initialize_sheets_service(self):
        """Initialize Google Sheets service and comprehensive sync service in background to avoid startup delays"""
        try:
            logger.info("🔧 Initializing Google Sheets service in background...")
            # Run Google Sheets initialization in thread pool to avoid blocking
            self.sheets_service = await asyncio.to_thread(GoogleSheetsService)
            logger.info("✅ Google Sheets service initialized successfully")

            # Initialize comprehensive sync service in thread pool to avoid blocking
            logger.info("🔧 Initializing comprehensive sync service...")
            # Import the comprehensive sync service
            try:
                from comprehensive_sync import ComprehensiveSyncService
                
                # Run comprehensive sync service initialization in thread pool
                self.comprehensive_sync_service = await asyncio.to_thread(
                    self._initialize_comprehensive_sync_in_thread
                )
                logger.info("✅ Comprehensive sync service initialized successfully")
            except ImportError as e:
                logger.warning(f"⚠️ Could not import comprehensive sync service: {e}")
                logger.info("📝 Will use individual sync methods instead")
            except Exception as e:
                logger.error(f"❌ Failed to initialize comprehensive sync service: {e}")
                logger.info("📝 Will use individual sync methods instead")

            self.sync_stats['health_status'] = 'healthy'
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Sheets service: {e}")
            self.sync_stats['health_status'] = 'unhealthy'
            self.sync_stats['last_error'] = str(e)
            self.sync_stats['last_error_time'] = datetime.utcnow()
            self.sheets_service = None
            self.comprehensive_sync_service = None
    
    async def stop_background_sync(self):
        """Stop the background sync service with proper cleanup"""
        if not self.is_running:
            return
        
        logger.info("🛑 Stopping enhanced background sync service...")
        self.is_running = False
        self.sync_stats['health_status'] = 'stopped'
        
        # Cancel health monitoring task
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        # Cancel main sync task
        if self.sync_task:
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass
        
        # Calculate uptime
        if self.sync_stats['start_time']:
            uptime = datetime.utcnow() - self.sync_stats['start_time']
            self.sync_stats['uptime_seconds'] = uptime.total_seconds()
        
        logger.info("✅ Enhanced background sync service stopped")
        logger.info(f"📊 Service uptime: {self.sync_stats['uptime_seconds']:.0f} seconds")
        logger.info(f"🔄 Total syncs: {self.sync_stats['total_syncs']}")
        logger.info(f"✅ Successful syncs: {self.sync_stats['successful_syncs']}")
        logger.info(f"❌ Failed syncs: {self.sync_stats['failed_syncs']}")
    
    async def _sync_loop(self):
        """Enhanced main sync loop with better error handling, recovery, and proper delays"""
        logger.info("🔄 Starting sync loop...")

        while self.is_running:
            try:
                # Use asyncio.sleep(0) to yield control to other tasks
                await asyncio.sleep(0)

                # Skip sync if paused for user requests
                if self.paused_for_requests:
                    logger.debug("⏸️ Sync paused for user requests, checking again in 10 seconds")
                    await asyncio.sleep(10)  # Check again in 10 seconds
                    continue

                # Skip sync if disabled
                if not self.sync_enabled:
                    logger.debug("⏸️ Sync disabled, checking again in 30 seconds")
                    await asyncio.sleep(30)  # Check again in 30 seconds
                    continue

                # Check if we should skip due to consecutive failures
                if self.consecutive_failures >= self.config.max_consecutive_failures:
                    logger.warning(f"⏸️ Too many consecutive failures ({self.consecutive_failures}), pausing sync for 5 minutes")
                    await asyncio.sleep(300)  # Wait 5 minutes before retrying
                    continue

                # Wait for any ongoing sync to complete before starting new one
                if self.sync_in_progress:
                    logger.debug("🔄 Sync already in progress, waiting for completion...")
                    # Wait a bit and check again
                    await asyncio.sleep(5)
                    continue

                # Calculate time until next sync
                if self.last_sync_time:
                    time_since_last_sync = (datetime.utcnow() - self.last_sync_time).total_seconds()
                    if time_since_last_sync < self.config.interval_seconds:
                        # Not yet time for next sync, wait a bit
                        wait_time = min(30, self.config.interval_seconds - time_since_last_sync)
                        logger.debug(f"⏰ Next sync in {wait_time:.0f} seconds")
                        await asyncio.sleep(wait_time)
                        continue

                # Perform sync
                logger.info("🚀 Starting scheduled sync cycle")
                await self._perform_sync()

                # Add a small delay after sync completion before checking again
                await asyncio.sleep(5)

            except asyncio.CancelledError:
                logger.info("🛑 Sync loop cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Critical error in sync loop: {e}")
                self.consecutive_failures += 1
                self.sync_stats['last_error'] = str(e)
                self.sync_stats['last_error_time'] = datetime.utcnow()
                # Wait before retrying
                await asyncio.sleep(60)
    
    async def _health_monitor_loop(self):
        """Monitor service health and log status periodically"""
        logger.info("🏥 Starting health monitoring...")
        
        while self.is_running:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                
                # Update uptime
                if self.sync_stats['start_time']:
                    uptime = datetime.utcnow() - self.sync_stats['start_time']
                    self.sync_stats['uptime_seconds'] = uptime.total_seconds()
                
                # Update health status
                if self.consecutive_failures >= self.config.max_consecutive_failures:
                    self.sync_stats['health_status'] = 'degraded'
                elif self.consecutive_failures > 0:
                    self.sync_stats['health_status'] = 'warning'
                else:
                    self.sync_stats['health_status'] = 'healthy'
                
                # Log health status
                success_rate = 0
                if self.sync_stats['total_syncs'] > 0:
                    success_rate = (self.sync_stats['successful_syncs'] / self.sync_stats['total_syncs']) * 100
                
                logger.info("🏥 Health Check - "                f"Status: {self.sync_stats['health_status']} | "
                f"Uptime: {self.sync_stats['uptime_seconds']:.0f}s | "
                f"Total: {self.sync_stats['total_syncs']} | "
                f"Success: {self.sync_stats['successful_syncs']} | "
                f"Failed: {self.sync_stats['failed_syncs']} | "
                f"Success Rate: {success_rate:.1f}%")
                
                self.last_health_check = datetime.utcnow()
                
            except asyncio.CancelledError:
                logger.info("🏥 Health monitoring cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Error in health monitoring: {e}")
                await asyncio.sleep(30)  # Wait before retrying
    
    async def _perform_sync(self):
        """Enhanced sync operation using comprehensive sync approach with proper delays and timeout"""
        if self.sync_in_progress:
            logger.debug("Sync already in progress, skipping this cycle")
            return

        # Check if sync is enabled
        if not self.sync_enabled:
            logger.debug("⏸️ Google Sheets sync is disabled, skipping sync")
            return

        # Check if services are initialized
        if self.sheets_service is None:
            logger.debug("⏳ Google Sheets service not yet initialized, skipping sync")
            return

        self.sync_in_progress = True
        sync_start_time = datetime.utcnow()
        sync_success = False

        try:
            logger.info("🔄 Starting comprehensive background sync to Google Sheets")
            self.sync_stats['total_syncs'] += 1

            # Yield control to other tasks
            await asyncio.sleep(0)

            # Use comprehensive sync service if available with timeout
            if self.comprehensive_sync_service:
                try:
                    logger.info("📊 Using comprehensive sync service for all tabs")

                    # Determine if we should do incremental sync
                    use_incremental = (self.last_sync_time is not None and
                                     self.config.enable_incremental_sync and
                                     (datetime.utcnow() - self.last_sync_time).total_seconds() < 3600)  # Only incremental if last sync was within 1 hour

                    # Perform comprehensive sync in separate thread to avoid blocking main thread
                    # This ensures that even heavy sync operations don't block user requests
                    logger.info("🧵 Running sync operation in separate thread to avoid blocking main thread")
                    sync_results = await asyncio.wait_for(
                        asyncio.to_thread(
                            self._run_sync_in_thread,
                            use_incremental
                        ),
                        timeout=300.0  # 5 minute timeout
                    )

                    # Log results for each tab
                    successful_tabs = 0
                    failed_tabs = 0

                    for tab_name, result in sync_results.items():
                        if result.get('synced') != 'error':
                            logger.info(f"✅ {tab_name}: {result.get('message', 'Synced successfully')}")
                            successful_tabs += 1
                        else:
                            logger.warning(f"❌ {tab_name}: {result.get('message', 'Sync failed')}")
                            failed_tabs += 1

                    # Add delay between sync operations
                    await asyncio.sleep(self.config.sync_delay_seconds)

                    # Consider sync successful if at least some tabs were synced
                    if successful_tabs > 0:
                        sync_success = True
                        self.last_sync_time = datetime.utcnow()
                        self.consecutive_failures = 0

                        sync_duration = (self.last_sync_time - sync_start_time).total_seconds()
                        self.sync_stats['last_sync_duration'] = sync_duration
                        self.sync_stats['successful_syncs'] += 1

                        # Update average duration
                        total_duration = self.sync_stats['total_sync_duration'] + sync_duration
                        self.sync_stats['total_sync_duration'] = total_duration
                        self.sync_stats['average_sync_duration'] = total_duration / self.sync_stats['successful_syncs']

                        logger.info(f"✅ Comprehensive sync successful: {successful_tabs} tabs synced, {failed_tabs} tabs failed in {sync_duration:.2f}s")
                    else:
                        logger.warning("⚠️ Comprehensive sync failed: no tabs were successfully synced")
                        self.consecutive_failures += 1

                except asyncio.TimeoutError:
                    logger.error("⏰ Comprehensive sync timed out after 5 minutes")
                    self.consecutive_failures += 1
                    # Fall back to individual sync methods
                    await self._perform_individual_sync(sync_start_time)
                except Exception as e:
                    logger.error(f"❌ Error in comprehensive sync: {e}")
                    self.consecutive_failures += 1
                    # Fall back to individual sync methods
                    await self._perform_individual_sync(sync_start_time)

            else:
                # Fall back to individual sync methods
                logger.info("📝 Using individual sync methods (comprehensive sync not available)")
                await self._perform_individual_sync(sync_start_time)

        except Exception as e:
            logger.error(f"❌ Error during background sync: {e}")
            self.consecutive_failures += 1
            self.sync_stats['last_error'] = str(e)
            self.sync_stats['last_error_time'] = datetime.utcnow()
        finally:
            self.sync_stats['failed_syncs'] = self.sync_stats['total_syncs'] - self.sync_stats['successful_syncs']
            self.sync_in_progress = False

            # Log sync completion
            if sync_success:
                logger.info("🎉 Background sync cycle completed successfully")
            else:
                logger.warning("⚠️ Background sync cycle completed with issues")

    async def _perform_individual_sync(self, sync_start_time: datetime):
        """Fallback method using individual sync operations with proper delays"""
        logger.info("📝 Performing individual sync operations...")
        sync_success = False

        try:
            # Sync course statistics if enabled
            if self.config.enable_course_stats:
                try:
                    from app.services.course_statistics_service import CourseStatisticsService
                    from app.services.course_statistics_sync_service import course_statistics_sync_service
                    stats_service = CourseStatisticsService()

                    # Update course statistics in database
                    stats_result = await stats_service.update_all_user_statistics()
                    logger.info(f"📚 Course statistics update: {stats_result['message']}")

                    # Add delay between operations
                    await asyncio.sleep(self.config.sync_delay_seconds)

                    # Sync course statistics to Google Sheets
                    course_success = await course_statistics_sync_service.sync_course_statistics_to_sheets()
                    if course_success:
                        logger.info("✅ Course statistics synced to Google Sheets")
                        sync_success = True
                    else:
                        logger.warning("⚠️ Course statistics sync failed")

                except Exception as e:
                    logger.warning(f"⚠️ Failed to update course statistics: {e}")

            # Add delay between operations
            await asyncio.sleep(self.config.sync_delay_seconds)

            # Sync user profiles if enabled
            if self.config.enable_user_profiles:
                try:
                    # Determine if we should do incremental or full sync
                    use_incremental = (self.last_sync_time is not None and
                                     self.config.enable_incremental_sync)

                    if use_incremental:
                        # Incremental sync - only get updated profiles
                        user_profiles = await self.sheets_service.get_all_user_profiles_for_export(
                            incremental=True,
                            last_sync_time=self.last_sync_time
                        )

                        if user_profiles:
                            # Use incremental update method
                            success = await self.sheets_service.update_user_profiles_incremental(user_profiles)
                        else:
                            logger.debug("No updated user profiles found for incremental sync")
                            success = True  # Not a failure if no updates needed
                    else:
                        # Full sync - get all profiles
                        user_profiles = await self.sheets_service.get_all_user_profiles_for_export(
                            incremental=False
                        )

                        if user_profiles:
                            # Use full export method
                            success = await self._export_with_retry(user_profiles)
                        else:
                            logger.debug("No user profiles found for full sync")
                            success = True  # Not a failure if no data to sync

                    if success:
                        self.last_sync_time = datetime.utcnow()
                        self.sync_stats['successful_syncs'] += 1
                        self.consecutive_failures = 0  # Reset consecutive failures
                        sync_duration = (self.last_sync_time - sync_start_time).total_seconds()
                        self.sync_stats['last_sync_duration'] = sync_duration

                        # Update average duration
                        total_duration = self.sync_stats['total_sync_duration'] + sync_duration
                        self.sync_stats['total_sync_duration'] = total_duration
                        self.sync_stats['average_sync_duration'] = total_duration / self.sync_stats['successful_syncs']

                        sync_type = "incremental" if use_incremental else "full"
                        logger.info(f"✅ User profiles sync successful: {len(user_profiles) if user_profiles else 0} profiles synced in {sync_duration:.2f}s ({sync_type})")
                        sync_success = True
                    else:
                        logger.warning("⚠️ User profiles sync failed after all retries")
                        self.consecutive_failures += 1

                except Exception as e:
                    logger.warning(f"⚠️ Could not sync user profiles: {e}")
                    self.consecutive_failures += 1

            # Add delay between operations
            await asyncio.sleep(self.config.sync_delay_seconds)

            # Sync quiz responses if enabled
            if self.config.enable_quiz_responses:
                try:
                    use_incremental = self.last_sync_time is not None
                    last_sync = self.last_sync_time if use_incremental else None
                    quiz_success = await self.sheets_service.sync_quiz_responses(last_sync)

                    if quiz_success:
                        logger.info("✅ Quiz responses synced to Google Sheets")
                        sync_success = True
                    else:
                        logger.warning("⚠️ Quiz responses sync failed")

                except Exception as e:
                    logger.warning(f"⚠️ Could not sync quiz responses: {e}")

            # Add delay between operations
            await asyncio.sleep(self.config.sync_delay_seconds)

            # Sync engagement logs if enabled
            if self.config.enable_engagement_logs:
                try:
                    use_incremental = self.last_sync_time is not None
                    last_sync = self.last_sync_time if use_incremental else None
                    engagement_success = await self.sheets_service.sync_engagement_logs(last_sync)

                    if engagement_success:
                        logger.info("✅ Engagement logs synced to Google Sheets")
                        sync_success = True
                    else:
                        logger.warning("⚠️ Engagement logs sync failed")

                except Exception as e:
                    logger.warning(f"⚠️ Could not sync engagement logs: {e}")

            # Add delay between operations
            await asyncio.sleep(self.config.sync_delay_seconds)

            # Sync course progress if enabled
            if self.config.enable_course_progress:
                try:
                    use_incremental = self.last_sync_time is not None
                    last_sync = self.last_sync_time if use_incremental else None
                    progress_success = await self.sheets_service.sync_course_progress(last_sync)

                    if progress_success:
                        logger.info("✅ Course progress synced to Google Sheets")
                        sync_success = True
                    else:
                        logger.warning("⚠️ Course progress sync failed")

                except Exception as e:
                    logger.warning(f"⚠️ Could not sync course progress: {e}")

            # If no operations were attempted, consider it successful
            if (not self.config.enable_course_stats and not self.config.enable_user_profiles and
                not self.config.enable_quiz_responses and not self.config.enable_engagement_logs and
                not self.config.enable_course_progress):
                sync_success = True
                logger.info("ℹ️ No sync operations enabled, skipping")

        except Exception as e:
            logger.error(f"❌ Error during individual sync: {e}")
            self.consecutive_failures += 1
            self.sync_stats['last_error'] = str(e)
            self.sync_stats['last_error_time'] = datetime.utcnow()

        return sync_success
    
    async def _export_with_retry(self, user_profiles: list) -> bool:
        """Export user profiles with enhanced retry logic and exponential backoff"""
        for attempt in range(self.config.max_retries):
            try:
                logger.info(f"📤 Export attempt {attempt + 1}/{self.config.max_retries}")
                success = await self.sheets_service.export_user_profiles_to_sheet(user_profiles)
                
                if success:
                    logger.info(f"✅ Export successful on attempt {attempt + 1}")
                    return True
                    
            except Exception as e:
                logger.warning(f"⚠️ Export attempt {attempt + 1} failed: {e}")
                
                # Don't wait after the last attempt
                if attempt < self.config.max_retries - 1:
                    # Exponential backoff with jitter
                    delay = self.config.retry_delay_seconds * (2 ** attempt)
                    logger.info(f"⏳ Waiting {delay} seconds before retry...")
                    await asyncio.sleep(delay)
        
        logger.error(f"❌ Export failed after {self.config.max_retries} attempts")
        return False
    
    def _initialize_comprehensive_sync_in_thread(self):
        """
        Initialize the comprehensive sync service in a separate thread.
        This method is designed to run in a thread pool via asyncio.to_thread().
        
        Returns:
            ComprehensiveSyncService: Initialized sync service
        """
        import asyncio
        from comprehensive_sync import ComprehensiveSyncService
        
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            logger.info(f"🧵 Thread {threading.current_thread().name}: Initializing comprehensive sync service")
            comprehensive_sync_service = ComprehensiveSyncService()
            
            # Initialize the service in this thread's event loop
            loop.run_until_complete(comprehensive_sync_service.initialize())
            
            logger.info(f"🧵 Thread {threading.current_thread().name}: Comprehensive sync service initialized")
            return comprehensive_sync_service
        finally:
            # Clean up the event loop
            loop.close()
    
    def _run_sync_in_thread(self, use_incremental: bool) -> dict:
        """
        Run the comprehensive sync operation in a separate thread to prevent blocking the main thread.
        This method is designed to run in a thread pool via asyncio.to_thread().
        
        Args:
            use_incremental: Whether to perform incremental sync
            
        Returns:
            dict: Sync results from all tabs
        """
        import asyncio
        
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run the sync operation in this thread's event loop
            logger.info(f"🧵 Thread {threading.current_thread().name}: Starting sync operation")
            sync_results = loop.run_until_complete(
                self.comprehensive_sync_service.sync_all_tabs(incremental=use_incremental)
            )
            logger.info(f"🧵 Thread {threading.current_thread().name}: Sync operation completed")
            return sync_results
        finally:
            # Clean up the event loop
            loop.close()

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
        """Get comprehensive sync status and statistics"""
        success_rate = 0
        if self.sync_stats['total_syncs'] > 0:
            success_rate = (self.sync_stats['successful_syncs'] / self.sync_stats['total_syncs']) * 100
        
        uptime_seconds = 0
        if self.sync_stats['start_time']:
            uptime = datetime.utcnow() - self.sync_stats['start_time']
            uptime_seconds = uptime.total_seconds()
        
        return {
            'is_running': self.is_running,
            'sync_in_progress': self.sync_in_progress,
            'sync_enabled': self.sync_enabled,
            'paused_for_requests': self.paused_for_requests,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'next_sync_in_seconds': self._get_next_sync_in_seconds(),
            'config': {
                'interval_seconds': self.config.interval_seconds,
                'max_retries': self.config.max_retries,
                'sync_delay_seconds': self.config.sync_delay_seconds,
                'enable_course_stats': self.config.enable_course_stats,
                'enable_user_profiles': self.config.enable_user_profiles,
                'enable_incremental_sync': self.config.enable_incremental_sync,
                'enable_quiz_responses': self.config.enable_quiz_responses,
                'enable_engagement_logs': self.config.enable_engagement_logs,
                'enable_chat_logs': self.config.enable_chat_logs,
                'enable_course_progress': self.config.enable_course_progress,
                'health_check_interval': self.config.health_check_interval,
                'max_consecutive_failures': self.config.max_consecutive_failures
            },
            'statistics': {
                'total_syncs': self.sync_stats['total_syncs'],
                'successful_syncs': self.sync_stats['successful_syncs'],
                'failed_syncs': self.sync_stats['failed_syncs'],
                'success_rate_percent': round(success_rate, 2),
                'last_sync_duration_seconds': round(self.sync_stats['last_sync_duration'], 2),
                'average_sync_duration_seconds': round(self.sync_stats['average_sync_duration'], 2),
                'consecutive_failures': self.consecutive_failures,
                'last_error': self.sync_stats['last_error'],
                'last_error_time': self.sync_stats['last_error_time'].isoformat() if self.sync_stats['last_error_time'] else None,
                'health_status': self.sync_stats['health_status'],
                'uptime_seconds': round(uptime_seconds, 0),
                'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None
            }
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
        
        next_sync_time = self.last_sync_time + timedelta(seconds=self.config.interval_seconds)
        now = datetime.utcnow()
        
        if next_sync_time > now:
            return int((next_sync_time - now).total_seconds())
        else:
            return 0

# Global instance
background_sync_service = BackgroundSyncService() 