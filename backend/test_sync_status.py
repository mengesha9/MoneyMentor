#!/usr/bin/env python3
"""
Test sync functionality
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from dotenv import load_dotenv
load_dotenv()

from app.services.google_sheets_service import GoogleSheetsService

async def test_sync():
    """Test the sync functionality"""
    print("🔄 Testing Google Sheets sync...")

    sheets = GoogleSheetsService()

    try:
        # Get user profiles
        profiles = await sheets.get_all_user_profiles_for_export()
        print(f"📊 Found {len(profiles)} user profiles")

        if profiles:
            print("👤 Sample profile keys:", list(profiles[0].keys()))

            # Try to sync to Google Sheets
            success = await sheets.export_user_profiles_to_sheet(profiles)
            print(f"✅ Sync result: {success}")

            if success:
                print("🎉 User profile sync is working!")
            else:
                print("❌ Sync failed")
        else:
            print("📭 No user profiles found in database")

    except Exception as e:
        print(f"❌ Error during sync test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sync())