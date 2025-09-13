#!/usr/bin/env python3
"""
Test registration flow to identify sync issues
"""
import asyncio
import sys
import os
import time
import logging

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_registration_flow():
    """Test the registration flow step by step"""
    print("=== REGISTRATION FLOW DEBUG TEST ===")
    
    # Import components
    from app.services.user_service import UserService
    from app.services.triggered_sync_service import triggered_sync_service
    from app.core.auth import create_user
    
    print("✅ Imports successful")
    
    # Create test user data
    test_email = f"debug_test_{int(time.time())}@example.com"
    print(f"Test email: {test_email}")
    
    # Step 1: Create user (as done in registration)
    print("\n=== STEP 1: CREATE USER ===")
    try:
        user = await create_user(
            email=test_email,
            password="TestPassword123!",
            first_name="Debug",
            last_name="Test"
        )
        if user:
            print(f"✅ User created: {user['id']}")
            user_id = user['id']
        else:
            print("❌ User creation failed")
            return
    except Exception as e:
        print(f"❌ User creation error: {e}")
        return
    
    # Step 2: Create user service
    print("\n=== STEP 2: CREATE USER SERVICE ===")
    user_service = UserService()
    print("✅ UserService created")
    
    # Step 3: Get/Create user profile (without background tasks first)
    print("\n=== STEP 3: GET USER PROFILE (NO BACKGROUND TASKS) ===")
    try:
        profile = await user_service.get_user_profile(user_id)
        if profile:
            print(f"✅ Profile created/retrieved: {profile.user_id}")
        else:
            print("❌ Profile creation failed")
    except Exception as e:
        print(f"❌ Profile error: {e}")
    
    # Step 4: Check sync status
    print("\n=== STEP 4: CHECK SYNC STATUS ===")
    print(f"Sync enabled: {triggered_sync_service.enabled}")
    print(f"Pending sync: {triggered_sync_service.pending_sync}")
    print(f"Last sync time: {triggered_sync_service.last_sync_time}")
    
    # Step 5: Manual sync trigger test
    print("\n=== STEP 5: MANUAL SYNC TRIGGER TEST ===")
    try:
        sync_triggered = triggered_sync_service.trigger_sync(f"user_profile_created_{user_id}")
        print(f"Sync triggered: {sync_triggered}")
        
        if sync_triggered:
            # Wait for sync
            wait_time = 0
            max_wait = 15
            
            while triggered_sync_service.pending_sync and wait_time < max_wait:
                await asyncio.sleep(1)
                wait_time += 1
                if wait_time % 3 == 0:
                    print(f"   Waiting for sync... ({wait_time}s)")
            
            if triggered_sync_service.pending_sync:
                print(f"⚠️  Sync still pending after {max_wait}s")
            else:
                print("✅ Sync completed")
                print(f"Last sync: {triggered_sync_service.last_sync_time}")
        
    except Exception as e:
        print(f"❌ Sync error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== ANALYSIS ===")
    print("1. User creation: ✅" if user else "1. User creation: ❌")
    print("2. Profile creation: ✅" if profile else "2. Profile creation: ❌")
    print("3. Sync trigger: ✅" if sync_triggered else "3. Sync trigger: ❌")
    
    if not sync_triggered:
        print("\n❌ ISSUE FOUND: Sync is not being triggered!")
        print("Possible causes:")
        print("- Sync service is disabled")
        print("- Cooldown period is active")
        print("- Error in sync trigger logic")

if __name__ == "__main__":
    asyncio.run(test_registration_flow())