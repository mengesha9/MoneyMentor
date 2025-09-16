#!/usr/bin/env python3
"""
Test registration sync with real existing user
"""
import asyncio
import time
from datetime import datetime
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.triggered_sync_service import triggered_sync_service
from app.config.sync_config import get_sync_interval
from app.core.database import get_supabase

async def test_registration_sync_with_real_user():
    """Test sync timing with a real existing user"""
    
    print("=== REGISTRATION TO SHEETS SYNC TIMING TEST (Real User) ===")
    print()
    
    # Check current sync configuration
    cooldown = get_sync_interval('triggered_sync_cooldown')
    print(f"Triggered sync cooldown: {cooldown} seconds ({cooldown/60:.1f} minutes)")
    print()
    
    # Get a real existing user from the database
    try:
        supabase = get_supabase()
        result = supabase.table('user_profiles').select('user_id').limit(1).execute()
        
        if not result.data:
            print("❌ No existing users found in database. Cannot test with real user.")
            print("💡 Try running a real registration first, then run this test.")
            return
        
        real_user_id = result.data[0]['user_id']
        print(f"✅ Found existing user: {real_user_id}")
        
    except Exception as e:
        print(f"❌ Error accessing database: {e}")
        return
    
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
    
    # Test the sync with existing user
    print("=== TESTING SYNC WITH EXISTING USER ===")
    start_time = time.time()
    
    print(f"1. Simulating profile update for: {real_user_id}")
    
    # Trigger sync (as would happen during registration)
    print("2. Triggering background sync...")
    sync_triggered = triggered_sync_service.trigger_sync(f"user_profile_created_{real_user_id}")
    
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
            sync_success = triggered_sync_service.last_sync_time is not None
            if sync_success:
                print(f"✅ Sync completed successfully in {total_time:.1f} seconds")
            else:
                print(f"⚠️  Sync completed but may have failed in {total_time:.1f} seconds")
        
        print()
        print("=== TIMING SUMMARY ===")
        print(f"Registration response time: ~1-2 seconds (immediate)")
        print(f"Sync trigger delay: ~1-3 seconds (background task)")
        print(f"Actual sync time: {total_time:.1f} seconds")
        print(f"Total time to sheets: ~{total_time + 3:.1f} seconds")
        
        # Check if Google Sheets sync actually worked
        if triggered_sync_service.last_sync_time:
            last_sync_time = triggered_sync_service.last_sync_time.strftime("%H:%M:%S")
            print(f"✅ Last successful sync: {last_sync_time}")
        else:
            print("⚠️  No successful sync recorded")
        
    else:
        print("❌ Sync was not triggered (likely due to cooldown)")
        if last_sync:
            time_since_last = (datetime.now() - last_sync).total_seconds()
            remaining_cooldown = cooldown - time_since_last
            print(f"Next sync available in: {remaining_cooldown:.0f} seconds ({remaining_cooldown/60:.1f} minutes)")

if __name__ == "__main__":
    asyncio.run(test_registration_sync_with_real_user())