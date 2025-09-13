#!/usr/bin/env python3
"""
Simple Backend Sync Test
Tests the background sync service directly in the backend
"""
import asyncio
import logging
import os
import sys
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_backend_sync():
    """Test the background sync service directly"""
    logger.info("🧪 Testing Background Sync Service in Backend")
    logger.info("=" * 60)

    try:
        # Import the background sync service
        from app.services.background_sync_service import BackgroundSyncService

        # Create and start the service
        sync_service = BackgroundSyncService()

        logger.info("🚀 Starting background sync service...")
        await sync_service.start_background_sync()

        # Let it run for 2 minutes to see the sync in action
        logger.info("⏳ Letting service run for 2 minutes to test functionality...")
        await asyncio.sleep(120)  # 2 minutes

        # Stop the service
        logger.info("🛑 Stopping background sync service...")
        await sync_service.stop_background_sync()

        # Show final statistics
        stats = sync_service.sync_stats
        logger.info("=" * 60)
        logger.info("📊 FINAL SYNC STATISTICS:")
        logger.info(f"   Total Syncs: {stats['total_syncs']}")
        logger.info(f"   Successful: {stats['successful_syncs']}")
        logger.info(f"   Failed: {stats['failed_syncs']}")
        logger.info(f"   Health Status: {stats['health_status']}")
        logger.info(f"   Uptime: {stats['uptime_seconds']:.0f} seconds")
        logger.info(f"   Average Duration: {stats['average_sync_duration']:.2f} seconds")

        if stats['successful_syncs'] > 0:
            logger.info("✅ Backend sync test completed successfully!")
            return True
        else:
            logger.warning("⚠️ No successful syncs completed during test")
            return False

    except Exception as e:
        logger.error(f"❌ Backend sync test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_backend_sync())
    sys.exit(0 if success else 1)