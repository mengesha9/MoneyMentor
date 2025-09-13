#!/usr/bin/env python3
"""
Test frontend registration sync
Simulates the exact API call that frontend makes
"""
import asyncio
import json
import time
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_frontend_registration():
    """Test registration as called from frontend"""
    print("=== FRONTEND REGISTRATION SYNC TEST ===")
    print()
    
    # Import here to avoid path issues
    from fastapi import BackgroundTasks
    from app.api.routes.user import register_user
    from app.models.schemas import UserCreate
    from app.services.triggered_sync_service import triggered_sync_service
    
    # Reset sync state
    triggered_sync_service.last_sync_time = None
    triggered_sync_service.pending_sync = False
    
    # Create a test user data (like frontend would send)
    test_user_data = UserCreate(
        email=f"test_{int(time.time())}@example.com",
        password="TestPassword123!",
        first_name="Test",
        last_name="User"
    )
    
    print(f"Test user email: {test_user_data.email}")
    print()
    
    # Create background tasks (like FastAPI would)
    background_tasks = BackgroundTasks()
    
    print("=== CALLING REGISTRATION ENDPOINT ===")
    start_time = time.time()
    
    try:
        # Call the registration endpoint exactly as frontend would
        response = await register_user(test_user_data, background_tasks)
        
        registration_time = time.time() - start_time
        print(f"✅ Registration completed in {registration_time:.2f} seconds")
        print(f"User ID: {response.user.id}")
        print(f"Profile created: {'Yes' if response.profile else 'No'}")
        print()
        
        # Check if background tasks were scheduled
        if background_tasks.tasks:
            print(f"✅ Background tasks scheduled: {len(background_tasks.tasks)}")
            
            # Execute background tasks (simulating FastAPI execution)
            print("=== EXECUTING BACKGROUND TASKS ===")
            for task in background_tasks.tasks:
                print(f"Executing task: {task.func.__name__}")
                try:
                    if asyncio.iscoroutinefunction(task.func):
                        await task.func(*task.args, **task.kwargs)
                    else:
                        task.func(*task.args, **task.kwargs)
                    print(f"✅ Task completed")
                except Exception as e:
                    print(f"❌ Task failed: {e}")
            
            # Wait for sync to complete
            print("=== WAITING FOR SYNC COMPLETION ===")
            wait_time = 0
            max_wait = 30
            
            while triggered_sync_service.pending_sync and wait_time < max_wait:
                await asyncio.sleep(1)
                wait_time += 1
                if wait_time % 5 == 0:
                    print(f"   Still syncing... ({wait_time}s elapsed)")
            
            total_time = time.time() - start_time
            
            if triggered_sync_service.pending_sync:
                print(f"⚠️  Sync still pending after {max_wait} seconds")
            else:
                print(f"✅ Complete process finished in {total_time:.1f} seconds")
                
                if triggered_sync_service.last_sync_time:
                    print(f"✅ Last sync completed at: {triggered_sync_service.last_sync_time.strftime('%H:%M:%S')}")
                else:
                    print("⚠️  No sync time recorded")
        else:
            print("❌ No background tasks were scheduled!")
            print("This means sync won't happen!")
        
        print()
        print("=== SYNC ANALYSIS ===")
        print(f"Sync enabled: {triggered_sync_service.enabled}")
        print(f"Pending sync: {triggered_sync_service.pending_sync}")
        print(f"Last sync time: {triggered_sync_service.last_sync_time}")
        
    except Exception as e:
        print(f"❌ Registration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_frontend_registration())