#!/usr/bin/env python3
"""
Test registration sync timing
"""
import asyncio
import time
import uuid
from datetime import datetime
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.user_service import UserService
from app.services.triggered_sync_service import triggered_sync_service
from app.config.sync_config import get_sync_interval

async def test_registration_sync_timing():
    """Test how long it takes for a user to appear in sheets after registration"""
    
    print("=== REGISTRATION TO SHEETS SYNC TIMING TEST ===")
    print()
    
    # Check current sync configuration
    cooldown = get_sync_interval('triggered_sync_cooldown')
    print(f"Triggered sync cooldown: {cooldown} seconds ({cooldown/60:.1f} minutes)")
    print()
    
    # Check last sync time
    last_sync = triggered_sync_service.last_sync_time
    if last_sync:
        time_since_last = (datetime.now() - last_sync).total_seconds()
        print(f"Last sync was: {time_since_last:.0f} seconds ago")
        
        if time_since_last < cooldown:
            remaining_cooldown = cooldown - time_since_last
            print(f"⏳ Next sync will be delayed by: {remaining_cooldown:.0f} seconds")
        else:
            print("✅ No cooldown delay - sync will happen immediately")
    else:
        print("✅ No previous sync - sync will happen immediately")
    
    print()
    
    # Simulate registration sync trigger
    print("=== SIMULATING USER REGISTRATION SYNC ===")
    start_time = time.time()
    
    # This is what happens during registration - use a real UUID format
    fake_user_id = str(uuid.uuid4())  # Generate a valid UUID
    print(f"1. User registered: {fake_user_id}")
    
    # Trigger sync (as background task in real registration)
    print("2. Triggering background sync...")
    sync_triggered = triggered_sync_service.trigger_sync(f"user_profile_created_{fake_user_id}")
    
    if sync_triggered:
        print("✅ Sync triggered successfully")
        
        # Wait for sync to complete
        print("3. Waiting for sync to complete...")
        
        # Check sync status periodically
        max_wait = 60  # Maximum 60 seconds
        wait_time = 0
        
        while triggered_sync_service.pending_sync and wait_time < max_wait:
            await asyncio.sleep(1)
            wait_time += 1
            if wait_time % 5 == 0:
                print(f"   Still syncing... ({wait_time}s elapsed)")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        if triggered_sync_service.pending_sync:
            print(f"⚠️  Sync still pending after {max_wait} seconds")
        else:
            print(f"✅ Sync completed in {total_time:.1f} seconds")
        
        print()
        print("=== TIMING SUMMARY ===")
        print(f"Registration response time: ~1-2 seconds (immediate)")
        print(f"Sync trigger delay: ~1-3 seconds (background task)")
        print(f"Actual sync time: {total_time:.1f} seconds")
        print(f"Total time to sheets: ~{total_time + 3:.1f} seconds")
        
        if cooldown > 0 and last_sync:
            time_since_last = (datetime.now() - last_sync).total_seconds()
            if time_since_last < cooldown:
                remaining_cooldown = cooldown - time_since_last
                print(f"Note: With cooldown, actual delay could be up to {remaining_cooldown/60:.1f} minutes")
    
    else:
        print("❌ Sync was not triggered (likely due to cooldown)")
        if last_sync:
            time_since_last = (datetime.now() - last_sync).total_seconds()
            remaining_cooldown = cooldown - time_since_last
            print(f"Next sync available in: {remaining_cooldown:.0f} seconds ({remaining_cooldown/60:.1f} minutes)")

if __name__ == "__main__":
    asyncio.run(test_registration_sync_timing())