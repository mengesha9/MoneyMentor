#!/usr/bin/env python3
"""
Test script for the updated background sync service
"""
import asyncio
import logging
import os
from datetime import datetime

# Set up environment
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './google-credentials.json'
os.environ['GOOGLE_SHEETS_SPREADSHEET_ID'] = '1vAQcl58-j_EWD02F7Dw3YPGBY9OurKXs5hV8EMxg10I'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_background_sync():
    """Test the updated background sync service"""
    try:
        logger.info("🧪 Testing updated background sync service...")

        # Import the background sync service
        from app.services.background_sync_service import background_sync_service

        # Start the service
        logger.info("🚀 Starting background sync service...")
        await background_sync_service.start_background_sync()

        # Let it run for a short time to test
        logger.info("⏳ Letting service run for 30 seconds to test functionality...")
        await asyncio.sleep(30)

        # Get status
        status = background_sync_service.get_sync_status()
        logger.info("📊 Service Status:")
        logger.info(f"  - Running: {status['is_running']}")
        logger.info(f"  - Sync in progress: {status['sync_in_progress']}")
        logger.info(f"  - Total syncs: {status['statistics']['total_syncs']}")
        logger.info(f"  - Successful syncs: {status['statistics']['successful_syncs']}")
        logger.info(f"  - Failed syncs: {status['statistics']['failed_syncs']}")
        logger.info(f"  - Health status: {status['statistics']['health_status']}")
        logger.info(f"  - Sync interval: {status['config']['interval_seconds']} seconds")
        logger.info(f"  - Sync delay: {status['config']['sync_delay_seconds']} seconds")

        # Stop the service
        logger.info("🛑 Stopping background sync service...")
        await background_sync_service.stop_background_sync()

        logger.info("✅ Background sync service test completed successfully!")

    except Exception as e:
        logger.error(f"❌ Error testing background sync service: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_background_sync())