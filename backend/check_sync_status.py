#!/usr/bin/env python3
"""
Check sync service status
"""
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def check_sync_status():
    """Check if sync services are working"""
    print("=== SYNC SERVICE STATUS CHECK ===")
    
    try:
        from app.services.triggered_sync_service import triggered_sync_service
        from app.config.sync_config import get_sync_setting, get_sync_interval
        
        print("✅ Imports successful")
        
        # Check configuration
        print("\n=== CONFIGURATION ===")
        print(f"Triggered sync enabled: {get_sync_setting('enable_triggered_sync')}")
        print(f"Sync on profile create: {get_sync_setting('sync_on_profile_create')}")
        print(f"Cooldown period: {get_sync_interval('triggered_sync_cooldown')} seconds")
        
        # Check service state
        print("\n=== SERVICE STATE ===")
        print(f"Service enabled: {triggered_sync_service.enabled}")
        print(f"Pending sync: {triggered_sync_service.pending_sync}")
        print(f"Last sync time: {triggered_sync_service.last_sync_time}")
        print(f"Cooldown seconds: {triggered_sync_service.sync_cooldown}")
        
        # Test sync trigger
        print("\n=== TEST SYNC TRIGGER ===")
        result = triggered_sync_service.trigger_sync("test_check")
        print(f"Trigger result: {result}")
        
        if not result:
            if triggered_sync_service.pending_sync:
                print("❌ Sync already pending")
            elif triggered_sync_service.last_sync_time:
                from datetime import datetime
                time_since = (datetime.now() - triggered_sync_service.last_sync_time).total_seconds()
                if time_since < triggered_sync_service.sync_cooldown:
                    remaining = triggered_sync_service.sync_cooldown - time_since
                    print(f"❌ Cooldown active: {remaining:.0f} seconds remaining")
                else:
                    print("❌ Other issue preventing sync")
            else:
                print("❌ Unknown reason for sync failure")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_sync_status()