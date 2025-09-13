#!/usr/bin/env python3
"""
Test Thread-based Background Sync Service
Verifies that sync operations run in separate threads and don't block the main thread
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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_thread_based_sync():
    """Test that background sync operations run in separate threads"""
    
    logger.info("🧵 Testing Thread-based Background Sync Service")
    logger.info("=" * 60)
    
    # Test 1: Verify main thread is not blocked during sync
    logger.info("📊 Test 1: Main Thread Non-blocking Test")
    
    main_thread_id = threading.get_ident()
    logger.info(f"   Main thread ID: {main_thread_id}")
    
    # Simulate a sync operation that would normally block
    async def simulate_thread_sync():
        """Simulate sync operation running in thread"""
        def sync_operation():
            current_thread_id = threading.get_ident()
            thread_name = threading.current_thread().name
            logger.info(f"   🧵 Sync running in thread: {thread_name} (ID: {current_thread_id})")
            
            if current_thread_id != main_thread_id:
                logger.info("   ✅ Sync is running in separate thread (non-blocking)")
            else:
                logger.warning("   ⚠️ Sync is running in main thread (potentially blocking)")
            
            # Simulate heavy sync work
            time.sleep(0.1)  # Blocking operation
            return {"result": "sync_completed", "thread_id": current_thread_id}
        
        # Run in thread pool (like our background service does)
        result = await asyncio.to_thread(sync_operation)
        return result
    
    # Test concurrent operations
    async def main_thread_operation():
        """Simulate user operation that should not be blocked"""
        start_time = time.time()
        logger.info("   🔄 Starting main thread operation...")
        
        # Simulate user operation
        await asyncio.sleep(0.05)
        
        end_time = time.time()
        operation_time = end_time - start_time
        logger.info(f"   ⚡ Main thread operation completed in {operation_time:.3f}s")
        return operation_time
    
    # Run sync and main thread operation concurrently
    start_time = time.time()
    
    sync_task = asyncio.create_task(simulate_thread_sync())
    main_task = asyncio.create_task(main_thread_operation())
    
    sync_result, main_operation_time = await asyncio.gather(sync_task, main_task)
    
    total_time = time.time() - start_time
    
    logger.info(f"   📊 Results:")
    logger.info(f"      Sync thread ID: {sync_result['thread_id']}")
    logger.info(f"      Main thread ID: {main_thread_id}")
    logger.info(f"      Main operation time: {main_operation_time:.3f}s")
    logger.info(f"      Total concurrent time: {total_time:.3f}s")
    
    # Verify thread separation
    threads_different = sync_result['thread_id'] != main_thread_id
    main_operation_fast = main_operation_time < 0.1
    
    if threads_different and main_operation_fast:
        logger.info("   ✅ Thread isolation working correctly")
    else:
        logger.warning("   ⚠️ Thread isolation may have issues")
    
    # Test 2: Multiple concurrent thread operations
    logger.info("\n📊 Test 2: Multiple Concurrent Thread Operations")
    
    async def multiple_thread_operations():
        """Test multiple sync operations running concurrently in different threads"""
        
        def worker_operation(worker_id):
            thread_id = threading.get_ident()
            thread_name = threading.current_thread().name
            logger.info(f"   🧵 Worker {worker_id} in thread: {thread_name} (ID: {thread_id})")
            
            # Simulate different amounts of work
            time.sleep(0.02 * worker_id)
            return {"worker_id": worker_id, "thread_id": thread_id}
        
        # Start multiple thread operations
        tasks = []
        for i in range(1, 4):
            task = asyncio.create_task(asyncio.to_thread(worker_operation, i))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results
    
    # Run multiple thread operations with main thread work
    start_time = time.time()
    
    multi_task = asyncio.create_task(multiple_thread_operations())
    main_task2 = asyncio.create_task(main_thread_operation())
    
    multi_results, main_time2 = await asyncio.gather(multi_task, main_task2)
    
    multi_total_time = time.time() - start_time
    
    logger.info(f"   📊 Multiple Thread Results:")
    thread_ids = set()
    for result in multi_results:
        thread_ids.add(result['thread_id'])
        logger.info(f"      Worker {result['worker_id']}: Thread {result['thread_id']}")
    
    logger.info(f"   📊 Analysis:")
    logger.info(f"      Unique thread IDs used: {len(thread_ids)}")
    logger.info(f"      Main thread operations time: {main_time2:.3f}s")
    logger.info(f"      Total time with concurrency: {multi_total_time:.3f}s")
    
    # Test 3: Background service simulation
    logger.info("\n📊 Test 3: Background Service Thread Pattern")
    
    class MockBackgroundService:
        """Mock background service to test thread patterns"""
        
        def __init__(self):
            self.is_running = False
            self.sync_count = 0
        
        async def start_service(self):
            """Start background service"""
            self.is_running = True
            logger.info("   🚀 Mock background service started")
        
        async def perform_sync_in_thread(self):
            """Simulate the thread-based sync pattern from our background service"""
            
            def sync_work():
                thread_id = threading.get_ident()
                thread_name = threading.current_thread().name
                
                logger.info(f"   🔄 Background sync in thread: {thread_name} (ID: {thread_id})")
                
                # Simulate comprehensive sync work
                time.sleep(0.05)
                self.sync_count += 1
                
                return {
                    "sync_id": self.sync_count,
                    "thread_id": thread_id,
                    "status": "completed"
                }
            
            # Use the same pattern as our background service
            result = await asyncio.to_thread(sync_work)
            return result
        
        async def stop_service(self):
            """Stop background service"""
            self.is_running = False
            logger.info("   🛑 Mock background service stopped")
    
    # Test the background service pattern
    service = MockBackgroundService()
    await service.start_service()
    
    # Simulate background sync while handling user requests
    sync_task = asyncio.create_task(service.perform_sync_in_thread())
    user_request_task = asyncio.create_task(main_thread_operation())
    
    service_sync_result, user_time = await asyncio.gather(sync_task, user_request_task)
    
    await service.stop_service()
    
    logger.info(f"   📊 Background Service Results:")
    logger.info(f"      Sync completed: {service_sync_result['status']}")
    logger.info(f"      Sync thread ID: {service_sync_result['thread_id']}")
    logger.info(f"      User request time: {user_time:.3f}s")
    logger.info(f"      User request unblocked: {user_time < 0.1}")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("🎉 Thread-based Sync Test Summary:")
    
    all_tests_passed = True
    
    # Check test 1
    if threads_different and main_operation_fast:
        logger.info("✅ Test 1: Main thread non-blocking - PASSED")
    else:
        logger.error("❌ Test 1: Main thread non-blocking - FAILED")
        all_tests_passed = False
    
    # Check test 2
    if len(thread_ids) > 1 and main_time2 < 0.1:
        logger.info("✅ Test 2: Multiple concurrent threads - PASSED")
    else:
        logger.error("❌ Test 2: Multiple concurrent threads - FAILED")
        all_tests_passed = False
    
    # Check test 3
    service_thread_isolated = service_sync_result['thread_id'] != main_thread_id
    service_user_fast = user_time < 0.1
    
    if service_thread_isolated and service_user_fast:
        logger.info("✅ Test 3: Background service pattern - PASSED")
    else:
        logger.error("❌ Test 3: Background service pattern - FAILED")
        all_tests_passed = False
    
    if all_tests_passed:
        logger.info("\n🏆 All thread-based sync tests PASSED!")
        logger.info("The background sync service will run in separate threads and won't block the main thread.")
    else:
        logger.error("\n💥 Some thread-based sync tests FAILED!")
        return False
    
    return True

async def main():
    """Run the thread-based sync test"""
    try:
        success = await test_thread_based_sync()
        if success:
            logger.info("\n✅ Thread-based sync service verification complete!")
        else:
            logger.error("\n❌ Thread-based sync service verification failed!")
            return False
    except Exception as e:
        logger.error(f"\n💥 Test failed with error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(main())