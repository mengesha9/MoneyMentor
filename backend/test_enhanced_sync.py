#!/usr/bin/env python3
"""
Test the enhanced background sync service
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from dotenv import load_dotenv
load_dotenv()

from app.services.background_sync_service import BackgroundSyncService, SyncConfig

async def test_enhanced_sync():
    """Test the enhanced background sync service"""
    print("🧪 Testing Enhanced Background Sync Service...")
    print("=" * 60)

    # Create custom config for testing
    config = SyncConfig(
        interval_seconds=30,  # 30 seconds for testing
        max_retries=2,
        enable_course_stats=True,
        enable_user_profiles=True
    )

    # Initialize service with custom config
    service = BackgroundSyncService(config)

    try:
        # Start the service
        print("🚀 Starting enhanced background sync service...")
        await service.start_background_sync()

        # Wait a bit to let it initialize
        await asyncio.sleep(5)

        # Check initial status
        status = service.get_sync_status()
        print("📊 Initial Status:")
        print(f"  Running: {status['is_running']}")
        print(f"  Health: {status['statistics']['health_status']}")
        print(f"  Config: {status['config']}")

        # Wait for a sync cycle
        print("⏳ Waiting for sync cycle...")
        await asyncio.sleep(35)  # Wait longer than the 30-second interval

        # Check status after sync
        status = service.get_sync_status()
        print("📊 Status After Sync:")
        print(f"  Total Syncs: {status['statistics']['total_syncs']}")
        print(f"  Successful: {status['statistics']['successful_syncs']}")
        print(f"  Failed: {status['statistics']['failed_syncs']}")
        print(f"  Success Rate: {status['statistics']['success_rate_percent']}%")
        print(f"  Last Duration: {status['statistics']['last_sync_duration_seconds']}s")
        print(f"  Health: {status['statistics']['health_status']}")

        # Test force sync
        print("🔄 Testing force sync...")
        force_success = await service.force_sync_now()
        print(f"  Force sync result: {force_success}")

        # Wait a bit more
        await asyncio.sleep(10)

        # Final status
        final_status = service.get_sync_status()
        print("📊 Final Status:")
        print(f"  Uptime: {final_status['statistics']['uptime_seconds']}s")
        print(f"  Total Syncs: {final_status['statistics']['total_syncs']}")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Stop the service
        print("🛑 Stopping service...")
        await service.stop_background_sync()
        print("✅ Test completed")

if __name__ == "__main__":
    asyncio.run(test_enhanced_sync())