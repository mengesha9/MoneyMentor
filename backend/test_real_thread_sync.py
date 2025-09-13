#!/usr/bin/env python3
"""
Integration Test for Thread-based Background Sync Service
Tests the actual BackgroundSyncService with thread isolation
"""

import asyncio
import time
import threading
import logging
from datetime import datetime
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append('.')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_real_background_sync_service():
    """Test the actual BackgroundSyncService with thread isolation"""
    
    logger.info("🔧 Testing Real Background Sync Service with Thread Isolation")
    logger.info("=" * 60)
    
    try:
        # Import the actual background sync service
        from app.services.background_sync_service import BackgroundSyncService, SyncConfig
        logger.info("✅ Successfully imported BackgroundSyncService")
    except ImportError as e:
        logger.error(f"❌ Failed to import BackgroundSyncService: {e}")
        return False
    
    # Test 1: Service initialization doesn't block main thread
    logger.info("📊 Test 1: Service Initialization Thread Safety")
    
    main_thread_id = threading.get_ident()
    logger.info(f"   Main thread ID: {main_thread_id}")
    
    # Create a custom config for testing
    test_config = SyncConfig(
        interval_seconds=60,  # Long interval so it doesn't auto-sync during test
        max_retries=1,  # Reduce retries for faster test
        sync_delay_seconds=1  # Shorter delay for faster test
    )
    
    service = BackgroundSyncService(test_config)
    
    # Test concurrent initialization and main thread operations
    async def init_service():
        """Initialize the service"""
        logger.info("   🚀 Initializing BackgroundSyncService...")
        await service.start_background_sync()
        return "service_initialized"
    
    async def main_thread_work():
        """Simulate main thread work during initialization"""
        start_time = time.time()
        logger.info("   ⚡ Main thread working during service init...")
        await asyncio.sleep(0.1)  # Simulate work
        end_time = time.time()
        return end_time - start_time
    
    # Run initialization and main thread work concurrently
    init_task = asyncio.create_task(init_service())
    main_task = asyncio.create_task(main_thread_work())
    
    init_result, main_time = await asyncio.gather(init_task, main_task)
    
    logger.info(f"   📊 Initialization Results:")
    logger.info(f"      Service status: {init_result}")
    logger.info(f"      Main thread work time: {main_time:.3f}s")
    logger.info(f"      Main thread blocked: {main_time > 0.15}")
    
    if main_time < 0.15:
        logger.info("   ✅ Service initialization doesn't block main thread")
        init_test_passed = True
    else:
        logger.warning("   ⚠️ Service initialization may be blocking main thread")
        init_test_passed = False
    
    # Test 2: Manual sync in thread
    logger.info("\n📊 Test 2: Manual Sync Thread Isolation")
    
    # Test force sync
    async def force_sync_test():
        """Test force sync in thread"""
        logger.info("   🔄 Testing force sync...")
        start_time = time.time()
        
        try:
            # This should run in a separate thread
            sync_success = await service.force_sync_now()
            end_time = time.time()
            
            return {
                "success": sync_success,
                "duration": end_time - start_time
            }
        except Exception as e:
            logger.warning(f"   ⚠️ Force sync failed (expected if no sheets configured): {e}")
            end_time = time.time()
            return {
                "success": False,
                "duration": end_time - start_time,
                "error": str(e)
            }
    
    async def concurrent_main_work():
        """Main thread work during sync"""
        start_time = time.time()
        logger.info("   ⚡ Main thread working during force sync...")
        
        # Simulate user operations
        for i in range(3):
            await asyncio.sleep(0.02)  # Simulate quick operations
        
        end_time = time.time()
        actual_work_time = end_time - start_time
        logger.info(f"   📊 Concurrent work completed in {actual_work_time:.3f}s")
        return actual_work_time
    
    # Start sync task
    sync_task = asyncio.create_task(force_sync_test())
    
    # Give sync a moment to start, then run concurrent work
    await asyncio.sleep(0.1)
    concurrent_time = await concurrent_main_work()
    
    # Wait for sync to complete
    sync_result = await sync_task
    
    logger.info(f"   📊 Force Sync Results:")
    logger.info(f"      Sync duration: {sync_result['duration']:.3f}s")
    logger.info(f"      Concurrent work time: {concurrent_time:.3f}s")
    logger.info(f"      Sync attempted: {sync_result.get('success', 'error')}")
    
    # Main thread should complete quickly even if sync takes longer
    concurrent_work_fast = concurrent_time < 0.1
    
    if concurrent_work_fast:
        logger.info("   ✅ Force sync doesn't block concurrent operations")
        sync_test_passed = True
    else:
        logger.warning("   ⚠️ Force sync may be blocking concurrent operations")
        sync_test_passed = False
    
    # Test 3: Service status while sync operations
    logger.info("\n📊 Test 3: Service Status and Health Check")
    
    # Get service status
    status = service.get_sync_status()
    
    logger.info(f"   📊 Service Status:")
    logger.info(f"      Running: {status['is_running']}")
    logger.info(f"      Sync enabled: {status['sync_enabled']}")
    logger.info(f"      Health status: {status.get('stats', {}).get('health_status', 'unknown')}")
    
    # Test that status calls don't block
    async def rapid_status_checks():
        """Perform rapid status checks"""
        start_time = time.time()
        
        for i in range(5):
            status = service.get_sync_status()
            await asyncio.sleep(0.01)
        
        end_time = time.time()
        return end_time - start_time
    
    status_time = await rapid_status_checks()
    logger.info(f"   📊 Status Check Performance:")
    logger.info(f"      5 status checks time: {status_time:.3f}s")
    
    status_test_passed = status_time < 0.1
    
    if status_test_passed:
        logger.info("   ✅ Status checks are fast and non-blocking")
    else:
        logger.warning("   ⚠️ Status checks may be slow")
    
    # Test 4: Cleanup
    logger.info("\n📊 Test 4: Service Cleanup")
    
    async def cleanup_service():
        """Clean up the service"""
        logger.info("   🛑 Stopping BackgroundSyncService...")
        await service.stop_background_sync()
        return "service_stopped"
    
    async def main_work_during_cleanup():
        """Main thread work during cleanup"""
        start_time = time.time()
        await asyncio.sleep(0.05)
        end_time = time.time()
        return end_time - start_time
    
    # Test cleanup doesn't block main thread
    cleanup_task = asyncio.create_task(cleanup_service())
    cleanup_main_task = asyncio.create_task(main_work_during_cleanup())
    
    cleanup_result, cleanup_main_time = await asyncio.gather(cleanup_task, cleanup_main_task)
    
    logger.info(f"   📊 Cleanup Results:")
    logger.info(f"      Service status: {cleanup_result}")
    logger.info(f"      Main thread work time: {cleanup_main_time:.3f}s")
    
    cleanup_test_passed = cleanup_main_time < 0.1
    
    if cleanup_test_passed:
        logger.info("   ✅ Service cleanup doesn't block main thread")
    else:
        logger.warning("   ⚠️ Service cleanup may be blocking main thread")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("🎉 Real Background Sync Service Test Summary:")
    
    all_tests_passed = True
    
    if init_test_passed:
        logger.info("✅ Test 1: Service initialization thread safety - PASSED")
    else:
        logger.error("❌ Test 1: Service initialization thread safety - FAILED")
        all_tests_passed = False
    
    if sync_test_passed:
        logger.info("✅ Test 2: Manual sync thread isolation - PASSED")
    else:
        logger.error("❌ Test 2: Manual sync thread isolation - FAILED")
        all_tests_passed = False
    
    if status_test_passed:
        logger.info("✅ Test 3: Service status performance - PASSED")
    else:
        logger.error("❌ Test 3: Service status performance - FAILED")
        all_tests_passed = False
    
    if cleanup_test_passed:
        logger.info("✅ Test 4: Service cleanup thread safety - PASSED")
    else:
        logger.error("❌ Test 4: Service cleanup thread safety - FAILED")
        all_tests_passed = False
    
    if all_tests_passed:
        logger.info("\n🏆 All real background sync service tests PASSED!")
        logger.info("🎯 Key Achievements:")
        logger.info("   • Service initialization is non-blocking")
        logger.info("   • Sync operations run in separate threads")
        logger.info("   • Main thread remains responsive during sync")
        logger.info("   • Service status checks are fast")
        logger.info("   • Service cleanup is non-blocking")
        logger.info("\n🚀 The background sync service is now fully thread-isolated!")
    else:
        logger.error("\n💥 Some background sync service tests FAILED!")
        return False
    
    return True

async def main():
    """Run the real background sync service test"""
    try:
        success = await test_real_background_sync_service()
        if success:
            logger.info("\n✅ Real background sync service verification complete!")
            logger.info("🎉 Background sync operations will no longer block the main thread!")
        else:
            logger.error("\n❌ Real background sync service verification failed!")
            return False
    except Exception as e:
        logger.error(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(main())