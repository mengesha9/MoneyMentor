#!/usr/bin/env python3
"""
Test script for optimized non-blocking sync
Verifies that sync operations don't block user operations
"""
import asyncio
import logging
import time
from datetime import datetime, timedelta

# Setup environment
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './google-credentials.json'
os.environ['GOOGLE_SHEETS_SPREADSHEET_ID'] = '1vAQcl58-j_EWD02F7Dw3YPGBY9OurKXs5hV8EMxg10I'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_user_operation():
    """Simulate user operations like login/register"""
    start_time = time.time()
    
    # Simulate database operations for user login/register
    await asyncio.sleep(0.1)  # Simulate auth check
    await asyncio.sleep(0.1)  # Simulate profile lookup
    await asyncio.sleep(0.1)  # Simulate session creation
    
    duration = time.time() - start_time
    logger.info(f"👤 User operation completed in {duration:.3f}s")
    return duration

async def test_concurrent_operations():
    """Test that user operations complete quickly even during sync"""
    logger.info("🚀 Testing concurrent user operations during sync...")
    
    # Start sync in background
    from comprehensive_sync import ComprehensiveSyncService
    sync_service = ComprehensiveSyncService()
    await sync_service.initialize()
    
    # Start sync task (don't await, let it run in background)
    sync_task = asyncio.create_task(sync_service.sync_all_tabs(incremental=False))
    
    # Give sync a moment to start
    await asyncio.sleep(1)
    
    # Run multiple user operations concurrently
    user_tasks = []
    for i in range(5):
        task = asyncio.create_task(test_user_operation())
        user_tasks.append(task)
        await asyncio.sleep(0.1)  # Stagger the operations
    
    # Wait for user operations to complete
    user_durations = await asyncio.gather(*user_tasks)
    
    # Check if user operations completed quickly
    max_duration = max(user_durations)
    avg_duration = sum(user_durations) / len(user_durations)
    
    logger.info(f"📊 User operation stats:")
    logger.info(f"   Max duration: {max_duration:.3f}s")
    logger.info(f"   Avg duration: {avg_duration:.3f}s")
    
    # User operations should complete quickly (under 1 second)
    if max_duration < 1.0:
        logger.info("✅ User operations remain fast during sync!")
    else:
        logger.warning("⚠️ User operations are slow during sync")
    
    # Let sync finish or timeout after 30 seconds
    try:
        await asyncio.wait_for(sync_task, timeout=30.0)
        logger.info("✅ Sync completed successfully")
    except asyncio.TimeoutError:
        logger.info("⏰ Sync timeout after 30s (expected for large dataset)")
        sync_task.cancel()
    
    return max_duration < 1.0

async def test_batch_processing():
    """Test that our batch processing works correctly"""
    logger.info("🔄 Testing batch processing optimization...")
    
    from comprehensive_sync import ComprehensiveSyncService
    sync_service = ComprehensiveSyncService()
    await sync_service.initialize()
    
    # Test user profiles sync (which should use bulk queries now)
    start_time = time.time()
    result = await sync_service._sync_user_profiles(None)
    duration = time.time() - start_time
    
    logger.info(f"📈 User profiles sync: {result}")
    logger.info(f"⏱️ Duration: {duration:.2f}s")
    
    return result

async def main():
    """Main test function"""
    logger.info("🧪 Starting optimized sync tests...")
    logger.info("=" * 60)
    
    # Test 1: Batch processing
    logger.info("\n🔸 Test 1: Batch Processing Optimization")
    await test_batch_processing()
    
    # Test 2: Concurrent operations
    logger.info("\n🔸 Test 2: Non-blocking during sync")
    concurrent_success = await test_concurrent_operations()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📋 TEST SUMMARY:")
    
    if concurrent_success:
        logger.info("✅ Non-blocking optimization: PASS")
    else:
        logger.info("❌ Non-blocking optimization: FAIL")
    
    logger.info("🎉 Optimized sync tests completed!")

if __name__ == "__main__":
    asyncio.run(main())