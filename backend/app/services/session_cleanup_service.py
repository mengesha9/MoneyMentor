import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from app.utils.session import cleanup_empty_sessions

logger = logging.getLogger(__name__)

class SessionCleanupService:
    """Background service to automatically clean up old empty sessions"""
    
    def __init__(self):
        self.is_running = False
        self.cleanup_task = None
        self.cleanup_interval_hours = 24  # Run cleanup every 24 hours
        self.days_old_threshold = 30  # Clean up sessions older than 30 days
        
    async def start_cleanup_service(self):
        """Start the background cleanup service"""
        if self.is_running:
            logger.warning("Session cleanup service is already running")
            return
            
        self.is_running = True
        logger.info("Starting session cleanup service")
        
        # Start the cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
    async def stop_cleanup_service(self):
        """Stop the background cleanup service"""
        if not self.is_running:
            logger.warning("Session cleanup service is not running")
            return
            
        self.is_running = False
        logger.info("Stopping session cleanup service")
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Session cleanup service stopped")
        
    async def _cleanup_loop(self):
        """Main cleanup loop"""
        while self.is_running:
            try:
                logger.info("Running scheduled session cleanup")
                
                # Perform cleanup
                result = await cleanup_empty_sessions(None, self.days_old_threshold)
                
                if result["deleted_count"] > 0:
                    logger.info(f"Cleaned up {result['deleted_count']} empty sessions older than {self.days_old_threshold} days")
                else:
                    logger.debug("No empty sessions found to clean up")
                    
                # Wait for next cleanup cycle
                await asyncio.sleep(self.cleanup_interval_hours * 3600)  # Convert hours to seconds
                
            except asyncio.CancelledError:
                logger.info("Session cleanup service cancelled")
                break
            except Exception as e:
                logger.error(f"Error in session cleanup loop: {e}")
                # Wait a shorter time before retrying
                await asyncio.sleep(3600)  # Wait 1 hour before retrying
                
    async def force_cleanup_now(self) -> Dict[str, Any]:
        """Force an immediate cleanup"""
        try:
            logger.info("Forcing immediate session cleanup")
            result = await cleanup_empty_sessions(None, self.days_old_threshold)
            
            return {
                "success": True,
                "deleted_count": result["deleted_count"],
                "cutoff_date": result.get("cutoff_date"),
                "message": f"Cleaned up {result['deleted_count']} empty sessions"
            }
            
        except Exception as e:
            logger.error(f"Failed to force cleanup: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Cleanup failed"
            }
            
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the cleanup service"""
        return {
            "is_running": self.is_running,
            "cleanup_interval_hours": self.cleanup_interval_hours,
            "days_old_threshold": self.days_old_threshold,
            "last_cleanup": getattr(self, 'last_cleanup', None)
        }
        
    def update_config(self, cleanup_interval_hours: int = None, days_old_threshold: int = None):
        """Update cleanup service configuration"""
        if cleanup_interval_hours is not None:
            self.cleanup_interval_hours = cleanup_interval_hours
            logger.info(f"Updated cleanup interval to {cleanup_interval_hours} hours")
            
        if days_old_threshold is not None:
            self.days_old_threshold = days_old_threshold
            logger.info(f"Updated cleanup threshold to {days_old_threshold} days")

# Global instance
session_cleanup_service = SessionCleanupService() 