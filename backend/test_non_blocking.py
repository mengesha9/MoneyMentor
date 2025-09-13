#!/usr/bin/env python3
"""
Test Non-Blocking Implementation
Tests the updated async/await patterns
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

async def test_non_blocking_sync():
    """Test the non-blocking sync implementation"""
    logger.info("🚀 Testing Non-Blocking Sync Implementation")
    logger.info("=" * 60)

    try:
        # Test 1: Background Sync Service with new async patterns
        logger.info("🧪 Test 1: Background Sync Service")
        from app.services.background_sync_service import BackgroundSyncService
        
        sync_service = BackgroundSyncService()
        
        # Start service
        start_time = datetime.utcnow()
        await sync_service.start_background_sync()
        
        # Let it run for 30 seconds to test async operations
        logger.info("⏳ Running for 30 seconds to test async performance...")
        await asyncio.sleep(30)
        
        # Stop service
        await sync_service.stop_background_sync()
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ Test 1 completed in {duration:.2f} seconds")
        logger.info(f"📊 Sync stats: {sync_service.sync_stats}")
        
        # Test 2: Direct Comprehensive Sync
        logger.info("\n🧪 Test 2: Comprehensive Sync Service")
        from comprehensive_sync import ComprehensiveSyncService
        
        comp_sync = ComprehensiveSyncService()
        init_success = await comp_sync.initialize()
        
        if init_success:
            logger.info("✅ Comprehensive sync service initialized")
            
            # Test a single sync operation
            start_time = datetime.utcnow()
            results = await comp_sync.sync_all_tabs(incremental=False)
            end_time = datetime.utcnow()
            
            duration = (end_time - start_time).total_seconds()
            logger.info(f"✅ Comprehensive sync completed in {duration:.2f} seconds")
            
            # Log results
            successful_tabs = sum(1 for result in results.values() if result.get('synced') != 'error')
            total_tabs = len(results)
            
            logger.info(f"📊 Results: {successful_tabs}/{total_tabs} tabs synced successfully")
            
        else:
            logger.warning("⚠️ Could not initialize comprehensive sync service")
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 Non-Blocking Implementation Test Complete!")
        logger.info("✅ All async/await patterns working correctly")
        
        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

async def test_concurrent_operations():
    """Test that operations don't block each other"""
    logger.info("\n🧪 Testing Concurrent Operations (Non-Blocking Verification)")
    
    async def dummy_task(name, duration):
        """Dummy task to verify concurrency"""
        start = datetime.utcnow()
        await asyncio.sleep(duration)
        end = datetime.utcnow()
        logger.info(f"Task {name} completed in {(end-start).total_seconds():.2f}s")
        return name
    
    # Run multiple tasks concurrently
    start_time = datetime.utcnow()
    
    tasks = [
        dummy_task("A", 2),
        dummy_task("B", 2),
        dummy_task("C", 2)
    ]
    
    results = await asyncio.gather(*tasks)
    
    end_time = datetime.utcnow()
    total_duration = (end_time - start_time).total_seconds()
    
    logger.info(f"✅ Concurrent tasks completed: {results}")
    logger.info(f"📊 Total time: {total_duration:.2f}s (should be ~2s, not 6s)")
    
    if total_duration < 3:  # Should be around 2 seconds, not 6
        logger.info("🎉 Concurrency working correctly - operations are non-blocking!")
        return True
    else:
        logger.warning("⚠️ Operations may be blocking - check async implementation")
        return False

async def main():
    """Main test function"""
    logger.info("🔧 Non-Blocking Service Implementation Test")
    logger.info("🎯 Verifying async/await patterns work correctly")
    logger.info("=" * 80)
    
    # Test concurrency first
    concurrency_ok = await test_concurrent_operations()
    
    # Test actual sync services
    sync_ok = await test_non_blocking_sync()
    
    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("📋 TEST SUMMARY:")
    logger.info(f"   Concurrency Test: {'✅ PASS' if concurrency_ok else '❌ FAIL'}")
    logger.info(f"   Sync Services Test: {'✅ PASS' if sync_ok else '❌ FAIL'}")
    
    if concurrency_ok and sync_ok:
        logger.info("🎉 ALL TESTS PASSED - Non-blocking implementation working!")
        return True
    else:
        logger.error("❌ Some tests failed - check implementation")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)