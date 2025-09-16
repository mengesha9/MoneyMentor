#!/usr/bin/env python3
"""
Google Sheets Setup Script
This script sets up the Google Sheets with all required tabs and headers
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.google_sheets_service import GoogleSheetsService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def setup_google_sheets():
    """Set up Google Sheets with all required tabs and configurations"""
    try:
        logger.info("🔧 Starting Google Sheets setup...")
        
        # Initialize Google Sheets service
        sheets_service = GoogleSheetsService()
        
        if not sheets_service.service:
            logger.error("❌ Failed to initialize Google Sheets service")
            return False
        
        # Test basic connection
        logger.info("🔍 Testing Google Sheets connection...")
        connection_test = sheets_service.test_connection()
        if not connection_test:
            logger.info("📋 Setting up Google Sheets tabs...")
            
            # Set up client access (creates all required tabs)
            setup_success = sheets_service.setup_client_access()
            
            if setup_success:
                logger.info("✅ Google Sheets setup completed successfully!")
                
                # Test connection again
                connection_test = sheets_service.test_connection()
                if connection_test:
                    logger.info("✅ All tabs are now accessible")
                else:
                    logger.warning("⚠️  Setup completed but some tabs may not be accessible")
                
                # Get sheet info
                sheet_info = sheets_service.get_sheet_info()
                if sheet_info:
                    logger.info(f"📊 Sheet Title: {sheet_info['title']}")
                    logger.info(f"📋 Available Tabs: {sheet_info['sheets']}")
                    logger.info(f"🔗 Spreadsheet ID: {sheet_info['spreadsheet_id']}")
                
                return True
            else:
                logger.error("❌ Failed to set up Google Sheets")
                return False
        else:
            logger.info("✅ Google Sheets is already properly configured!")
            
            # Get sheet info
            sheet_info = sheets_service.get_sheet_info()
            if sheet_info:
                logger.info(f"📊 Sheet Title: {sheet_info['title']}")
                logger.info(f"📋 Available Tabs: {sheet_info['sheets']}")
                logger.info(f"🔗 Spreadsheet ID: {sheet_info['spreadsheet_id']}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Google Sheets setup failed: {e}")
        return False

async def test_user_profile_sync():
    """Test syncing user profiles to the sheets"""
    try:
        logger.info("🧪 Testing user profile sync...")
        
        sheets_service = GoogleSheetsService()
        
        # Get user profiles for export
        user_profiles = await sheets_service.get_all_user_profiles_for_export()
        
        if not user_profiles:
            logger.info("📭 No user profiles found to sync")
            return True
        
        logger.info(f"👥 Found {len(user_profiles)} user profiles to sync")
        
        # Test export
        success = await sheets_service.export_user_profiles_to_sheet(user_profiles)
        
        if success:
            logger.info(f"✅ Successfully synced {len(user_profiles)} user profiles to Google Sheets")
            return True
        else:
            logger.error("❌ Failed to sync user profiles to Google Sheets")
            return False
            
    except Exception as e:
        logger.error(f"❌ User profile sync test failed: {e}")
        return False

async def main():
    """Main setup function"""
    logger.info("🚀 Starting Google Sheets setup and testing...")
    
    # Step 1: Set up Google Sheets
    setup_success = await setup_google_sheets()
    if not setup_success:
        logger.error("❌ Google Sheets setup failed. Cannot proceed.")
        return False
    
    # Step 2: Test user profile sync
    sync_success = await test_user_profile_sync()
    if not sync_success:
        logger.error("❌ User profile sync test failed.")
        return False
    
    logger.info("🎉 Google Sheets setup and testing completed successfully!")
    logger.info("\n" + "="*60)
    logger.info("✅ SETUP COMPLETE - Your Google Sheets is ready!")
    logger.info("📋 All required tabs have been created")
    logger.info("👥 User profile sync is working")
    logger.info("🔄 Registration sync should now work properly")
    logger.info("="*60)
    
    return True

if __name__ == "__main__":
    result = asyncio.run(main())
    if result:
        print("\n✅ SUCCESS: Google Sheets setup completed!")
        sys.exit(0)
    else:
        print("\n❌ FAILED: Google Sheets setup failed!")
        sys.exit(1)