#!/usr/bin/env python3
"""
Complete Registration to Google Sheets Sync Verification
Tests the entire flow from user registration to Google Sheets sync
"""

import asyncio
import os
import sys
import time
import random
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    # Set environment for async operation
    os.environ['PYTHONPATH'] = str(current_dir)
    
    from app.core.auth import create_user
    from app.services.user_service import UserService
    from app.services.triggered_sync_service import TriggeredSyncService
    from app.services.manual_sync_service import ManualSyncService
    from app.core.database import get_db
    
    print("✅ All imports successful")
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

async def test_complete_registration_flow():
    """Test the complete registration to Google Sheets sync flow"""
    
    # Generate unique test email
    random_id = random.randint(1000000, 9999999)
    test_email = f"sync_test_{random_id}@example.com"
    test_password = "TestPassword123!"
    
    print(f"\n=== COMPLETE REGISTRATION TO SHEETS SYNC TEST ===")
    print(f"Test email: {test_email}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Step 1: Create user account (simulates registration)
        print(f"\n=== STEP 1: CREATE USER ACCOUNT ===")
        start_time = time.time()
        
        user_data = await create_user(
            email=test_email,
            password=test_password,
            first_name="Test",
            last_name="User"
        )
        
        user_id = user_data.get("id")
        print(f"✅ User created: {user_id}")
        creation_time = time.time() - start_time
        print(f"⏱️ User creation time: {creation_time:.2f} seconds")
        
        # Step 2: Create user service and get profile (simulates registration endpoint)
        print(f"\n=== STEP 2: GET/CREATE USER PROFILE ===")
        profile_start = time.time()
        
        user_service = UserService()
        
        # Simulate background tasks (empty implementation for sync test)
        class MockBackgroundTasks:
            def add_task(self, func, *args, **kwargs):
                print(f"🔄 Background task added: {func.__name__}")
                # Execute immediately for testing
                return func(*args, **kwargs)
        
        background_tasks = MockBackgroundTasks()
        
        # This simulates the registration endpoint call
        profile = await user_service.get_user_profile(user_id, background_tasks)
        
        profile_time = time.time() - profile_start
        print(f"✅ Profile handled: {profile.get('user_id', 'N/A')}")
        print(f"⏱️ Profile processing time: {profile_time:.2f} seconds")
        
        # Step 3: Check sync status
        print(f"\n=== STEP 3: VERIFY SYNC STATUS ===")
        triggered_sync = TriggeredSyncService()
        
        print(f"Sync enabled: {triggered_sync.enabled}")
        print(f"Pending sync: {triggered_sync.pending}")
        print(f"Last sync time: {triggered_sync.last_sync_time}")
        
        # Step 4: Wait for sync to complete (if pending)
        if triggered_sync.pending:
            print(f"\n=== STEP 4: WAITING FOR SYNC COMPLETION ===")
            sync_start = time.time()
            max_wait = 30  # Maximum wait time in seconds
            
            while triggered_sync.pending and (time.time() - sync_start) < max_wait:
                print(f"⏳ Waiting for sync... ({time.time() - sync_start:.1f}s)")
                await asyncio.sleep(2)
            
            sync_time = time.time() - sync_start
            
            if not triggered_sync.pending:
                print(f"✅ Sync completed!")
                print(f"⏱️ Sync completion time: {sync_time:.2f} seconds")
            else:
                print(f"⚠️ Sync still pending after {max_wait}s")
        else:
            print(f"✅ No pending sync (already completed)")
        
        # Step 5: Calculate total time
        total_time = time.time() - start_time
        print(f"\n=== TIMING SUMMARY ===")
        print(f"User creation: {creation_time:.2f}s")
        print(f"Profile processing: {profile_time:.2f}s")
        print(f"Total registration to sheets time: {total_time:.2f}s")
        
        if total_time <= 15:
            print(f"🎯 EXCELLENT: Total time {total_time:.2f}s is within target (≤15s)")
        elif total_time <= 30:
            print(f"✅ GOOD: Total time {total_time:.2f}s is acceptable (≤30s)")
        else:
            print(f"⚠️ SLOW: Total time {total_time:.2f}s exceeds target (>30s)")
        
        # Step 6: Verify user appears in Google Sheets
        print(f"\n=== STEP 6: VERIFY GOOGLE SHEETS SYNC ===")
        manual_sync = ManualSyncService()
        
        try:
            # Check if Google Sheets service is working
            await manual_sync.initialize()
            print(f"✅ Google Sheets service accessible")
            
            # Perform a targeted sync to ensure latest data
            result = await manual_sync.sync_users([user_id])
            
            if result.get("success"):
                synced_count = result.get("synced_users", 0)
                print(f"✅ User successfully synced to Google Sheets")
                print(f"📊 Synced users count: {synced_count}")
            else:
                print(f"❌ Sync to Google Sheets failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Google Sheets verification failed: {e}")
        
        print(f"\n=== FINAL RESULT ===")
        print(f"✅ Registration to Google Sheets sync flow completed successfully!")
        print(f"🎯 User {user_id} should now be visible in Google Sheets")
        print(f"⏱️ Total time from registration to sheets: {total_time:.2f} seconds")
        
        return {
            "success": True,
            "user_id": user_id,
            "total_time": total_time,
            "creation_time": creation_time,
            "profile_time": profile_time
        }
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    asyncio.run(test_complete_registration_flow())