#!/usr/bin/env python3
"""
Full Comprehensive Sync Test Script
Tests the complete sync process from Supabase to Google Sheets
"""
import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('full_sync_test.log')
    ]
)
logger = logging.getLogger(__name__)

class FullSyncTester:
    """Test class for running full comprehensive sync"""

    def __init__(self):
        self.comprehensive_sync_service = None
        self.sync_results = {}
        self.start_time = None
        self.end_time = None

    async def initialize(self):
        """Initialize the comprehensive sync service"""
        try:
            logger.info("🔧 Initializing comprehensive sync service...")

            # Import and initialize the comprehensive sync service
            from comprehensive_sync import ComprehensiveSyncService

            self.comprehensive_sync_service = ComprehensiveSyncService()
            success = await self.comprehensive_sync_service.initialize()

            if success:
                logger.info("✅ Comprehensive sync service initialized successfully")
                return True
            else:
                logger.error("❌ Failed to initialize comprehensive sync service")
                return False

        except Exception as e:
            logger.error(f"❌ Error initializing sync service: {e}")
            return False

    async def run_full_sync(self) -> Dict[str, Any]:
        """Run the full comprehensive sync and return detailed results"""
        if not self.comprehensive_sync_service:
            return {"error": "Service not initialized"}

        self.start_time = datetime.utcnow()
        logger.info("🚀 Starting full comprehensive sync test...")

        try:
            # Run the sync
            results = await self.comprehensive_sync_service.sync_all_tabs(incremental=False)

            self.end_time = datetime.utcnow()
            self.sync_results = results

            # Process and log results
            await self._process_sync_results(results)

            return results

        except Exception as e:
            logger.error(f"❌ Full sync failed: {e}")
            return {"error": str(e)}

    async def _process_sync_results(self, results: Dict[str, Any]):
        """Process and log detailed sync results"""
        logger.info("📊 === FULL SYNC RESULTS ===")

        total_tabs = len(results)
        successful_tabs = 0
        failed_tabs = 0
        total_records_synced = 0

        for tab_name, result in results.items():
            if isinstance(result, dict):
                if result.get('synced') != 'error':
                    successful_tabs += 1
                    records = result.get('synced', 0)
                    total_records_synced += records if isinstance(records, int) else 0
                    logger.info(f"✅ {tab_name}: {result.get('message', 'Synced successfully')} - {records} records")
                else:
                    failed_tabs += 1
                    logger.error(f"❌ {tab_name}: {result.get('message', 'Sync failed')}")
            else:
                logger.warning(f"⚠️ {tab_name}: Unexpected result format - {result}")

        # Calculate duration
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0

        logger.info("📊 === SYNC SUMMARY ===")
        logger.info(f"⏱️ Total duration: {duration:.2f} seconds")
        logger.info(f"📁 Total tabs: {total_tabs}")
        logger.info(f"✅ Successful tabs: {successful_tabs}")
        logger.info(f"❌ Failed tabs: {failed_tabs}")
        logger.info(f"📊 Total records synced: {total_records_synced}")

        if successful_tabs == total_tabs:
            logger.info("🎉 ALL TABS SYNCED SUCCESSFULLY!")
        elif successful_tabs > 0:
            logger.warning(f"⚠️ PARTIAL SUCCESS: {successful_tabs}/{total_tabs} tabs synced")
        else:
            logger.error("❌ COMPLETE FAILURE: No tabs were synced successfully")

    async def verify_google_sheets_data(self):
        """Verify that data was actually written to Google Sheets"""
        logger.info("🔍 Verifying Google Sheets data...")

        try:
            if not self.comprehensive_sync_service or not self.comprehensive_sync_service.sheets_service:
                logger.error("❌ Cannot verify - services not available")
                return

            sheets_service = self.comprehensive_sync_service.sheets_service

            # Check each tab that should have been synced
            tabs_to_check = [
                'UserProfiles', 'QuizResponses', 'EngagementLogs',
                'ChatLogs', 'CourseProgress', 'course_statistics',
                'ConfidencePolls', 'UsageLogs'
            ]

            for tab_name in tabs_to_check:
                try:
                    # Try to read a few rows from each tab
                    range_name = f'{tab_name}!A1:Z10'
                    result = sheets_service.service.spreadsheets().values().get(
                        spreadsheetId=os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID'),
                        range=range_name
                    ).execute()

                    values = result.get('values', [])
                    if values and len(values) > 1:  # More than just header
                        logger.info(f"✅ {tab_name}: Found {len(values)-1} rows of data in Google Sheets")
                    elif values and len(values) == 1:
                        logger.info(f"ℹ️ {tab_name}: Only header row found in Google Sheets")
                    else:
                        logger.warning(f"⚠️ {tab_name}: No data found in Google Sheets")

                except Exception as e:
                    logger.error(f"❌ Error checking {tab_name} in Google Sheets: {e}")

        except Exception as e:
            logger.error(f"❌ Error verifying Google Sheets data: {e}")

async def main():
    """Main test function"""
    logger.info("🧪 Starting Full Comprehensive Sync Test")
    logger.info("=" * 60)

    tester = FullSyncTester()

    # Initialize
    if not await tester.initialize():
        logger.error("❌ Test failed - could not initialize services")
        return

    # Run full sync
    results = await tester.run_full_sync()

    # Verify data in Google Sheets
    await tester.verify_google_sheets_data()

    # Final summary
    logger.info("=" * 60)
    logger.info("🏁 Full Comprehensive Sync Test Completed")

    if 'error' in results:
        logger.error(f"❌ Test failed with error: {results['error']}")
        sys.exit(1)
    else:
        logger.info("✅ Test completed successfully")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())