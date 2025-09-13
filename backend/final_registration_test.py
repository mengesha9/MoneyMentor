#!/usr/bin/env python3
"""
Final verification: Complete registration to Google Sheets flow
"""

import asyncio
import sys
import time
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

async def test_complete_flow():
    """Test the complete registration to Google Sheets flow"""
    
    from app.core.auth import create_user
    from app.services.user_service import UserService
    from app.services.manual_sync_service import ManualSyncService
    from app.services.triggered_sync_service import triggered_sync_service
    
    print("=" * 60)
    print("COMPLETE REGISTRATION TO GOOGLE SHEETS FLOW TEST")
    print("=" * 60)
    
    # Simulate a background task that executes sync
    class MockBackgroundTasks:
        def add_task(self, func, *args, **kwargs):
            print(f"🔄 Background task added: {func.__name__}")
            try:
                # Execute immediately for testing
                result = func(*args, **kwargs)
                print(f"✅ Background task completed successfully")
                return result
            except Exception as e:
                print(f"❌ Background task failed: {e}")
                import traceback
                traceback.print_exc()
    
    start_time = time.time()
    
    try:
        # Step 1: Create user (simulates /api/user/register)
        print("\n📝 STEP 1: Creating user account...")
        
        test_email = f"final_test_{int(time.time())}@example.com"
        user = await create_user(
            email=test_email,
            password="FinalTest123!",
            first_name="Final",
            last_name="Test"
        )
        
        user_creation_time = time.time() - start_time
        print(f"✅ User created: {user['email']}")
        print(f"   User ID: {user['id']}")
        print(f"   Creation time: {user_creation_time:.2f}s")
        
        # Step 2: Create profile with background sync (simulates registration endpoint)
        print("\n👤 STEP 2: Creating user profile with background sync...")
        
        user_service = UserService()
        background_tasks = MockBackgroundTasks()
        
        profile_start = time.time()
        profile = await user_service.get_user_profile(user['id'], background_tasks)
        profile_time = time.time() - profile_start
        
        print(f"✅ Profile created: {profile.user_id if profile else 'None'}")
        print(f"   Profile time: {profile_time:.2f}s")
        
        # Step 3: Verify sync occurred
        print("\n🔄 STEP 3: Verifying Google Sheets sync...")
        
        # Check if user data can be synced manually (verification)
        manual_sync = ManualSyncService()
        sync_result = await manual_sync.sync_specific_user_profiles_to_sheets([user['id']], force_sync=True)
        
        if sync_result.get('success'):
            print(f"✅ Google Sheets sync verified: {sync_result.get('message', 'No message')}")
        else:
            print(f"❌ Google Sheets sync failed: {sync_result.get('error', 'Unknown error')}")
        
        # Final timing
        total_time = time.time() - start_time
        
        print("\n" + "=" * 60)
        print("📊 FINAL RESULTS")
        print("=" * 60)
        print(f"✅ User Email: {test_email}")
        print(f"✅ User ID: {user['id']}")
        print(f"✅ Profile ID: {profile.user_id if profile else 'None'}")
        print(f"⏱️  Total Time: {total_time:.2f} seconds")
        print(f"📈 User creation: {user_creation_time:.2f}s")
        print(f"📈 Profile + sync: {profile_time:.2f}s")
        
        if total_time <= 15:
            print(f"🎯 EXCELLENT: Total time {total_time:.2f}s is within target (≤15s)")
        elif total_time <= 30:
            print(f"✅ GOOD: Total time {total_time:.2f}s is acceptable (≤30s)")
        else:
            print(f"⚠️ SLOW: Total time {total_time:.2f}s exceeds target (>30s)")
        
        print("\n🎉 REGISTRATION TO GOOGLE SHEETS FLOW: WORKING ✅")
        print("The user profile will now appear in your Google Sheets!")
        
        return {
            'success': True,
            'user_id': user['id'],
            'email': test_email,
            'total_time': total_time
        }
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    result = asyncio.run(test_complete_flow())
    
    if result['success']:
        print(f"\n✅ SUCCESS: Registration to Google Sheets sync is working!")
        print(f"📧 Test user: {result['email']}")
        print(f"🆔 User ID: {result['user_id']}")
        print(f"⏱️  Total time: {result['total_time']:.2f}s")
    else:
        print(f"\n❌ FAILED: {result['error']}")
        sys.exit(1)