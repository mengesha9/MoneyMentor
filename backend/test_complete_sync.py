#!/usr/bin/env python3
"""
Test script to verify complete Google Sheets sync functionality
"""
import asyncio
import logging
import os
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_complete_sync():
    """Test complete sync of all tabs"""
    try:
        logger.info("🧪 Starting complete sync test...")

        # Import services
        from app.services.google_sheets_service import GoogleSheetsService
        from app.services.background_sync_service import BackgroundSyncService

        # Initialize services
        sheets_service = GoogleSheetsService()
        sync_service = BackgroundSyncService()

        # Test connection
        logger.info("Testing Google Sheets connection...")
        connection_ok = sheets_service.test_connection()
        if not connection_ok:
            logger.error("❌ Google Sheets connection failed")
            return False

        logger.info("✅ Google Sheets connection successful")

        # Get current sheet info
        sheet_info = sheets_service.get_sheet_info()
        if sheet_info:
            logger.info(f"📊 Current sheet: {sheet_info['title']}")
            logger.info(f"📋 Available tabs: {sheet_info['sheets']}")

        # Force a complete sync
        logger.info("🔄 Starting forced sync of all tabs...")
        sync_result = await sync_service.force_sync_now()

        if sync_result:
            logger.info("✅ Complete sync test successful!")
            return True
        else:
            logger.error("❌ Complete sync test failed")
            return False

    except Exception as e:
        logger.error(f"❌ Error during sync test: {e}")
        return False

async def test_individual_sync_methods():
    """Test individual sync methods"""
    try:
        logger.info("🧪 Testing individual sync methods...")

        from app.services.google_sheets_service import GoogleSheetsService
        sheets_service = GoogleSheetsService()

        # Test each sync method
        methods_to_test = [
            ('Quiz Responses', sheets_service.sync_quiz_responses),
            ('Engagement Logs', sheets_service.sync_engagement_logs),
            ('Chat Logs', sheets_service.sync_chat_logs),
            ('Course Progress', sheets_service.sync_course_progress),
        ]

        for method_name, method_func in methods_to_test:
            try:
                logger.info(f"Testing {method_name} sync...")
                result = await method_func()
                if result:
                    logger.info(f"✅ {method_name} sync successful")
                else:
                    logger.warning(f"⚠️ {method_name} sync failed")
            except Exception as e:
                logger.error(f"❌ Error testing {method_name}: {e}")

        logger.info("✅ Individual sync methods test completed")
        return True

    except Exception as e:
        logger.error(f"❌ Error during individual sync test: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("🚀 Starting Google Sheets sync comprehensive test")

    # Test individual methods first
    await test_individual_sync_methods()

    # Test complete sync
    await test_complete_sync()

    logger.info("🏁 Test completed")

if __name__ == "__main__":
    asyncio.run(main())