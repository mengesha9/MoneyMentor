#!/usr/bin/env python3
"""
Test course statistics sync
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from dotenv import load_dotenv
load_dotenv()

from app.services.course_statistics_sync_service import CourseStatisticsSyncService

async def test_course_sync():
    """Test course statistics sync"""
    print("📚 Testing course statistics sync...")

    service = CourseStatisticsSyncService()

    try:
        success = await service.sync_course_statistics_to_sheets()
        print(f"✅ Course statistics sync result: {success}")

        if success:
            print("🎉 Course statistics sync is working!")
        else:
            print("❌ Course statistics sync failed")

    except Exception as e:
        print(f"❌ Error during course sync test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_course_sync())