#!/usr/bin/env python3
"""
Test the sync functionality for the recently created user
"""

import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

async def test_sync_for_user():
    """Test sync for the user that was just created"""
    
    from app.services.manual_sync_service import ManualSyncService
    from app.services.triggered_sync_service import triggered_sync_service
    
    print("=== TESTING SYNC FOR RECENTLY CREATED USER ===")
    
    # Test the specific user that was just created
    user_id = '518db15e-12bf-4e42-bcbb-c7a14a5a6ba6'
    print(f"Testing sync for user: {user_id}")
    
    try:
        # Test manual sync service directly
        manual_sync = ManualSyncService()
        print("✅ Manual sync service created")
        
        # Sync the specific user (this will initialize the sheets service automatically)
        result = await manual_sync.sync_specific_user_profiles_to_sheets([user_id], force_sync=True)
        
        if result.get('success'):
            print(f"✅ Sync successful: {result.get('message', 'No message')}")
            synced_users = result.get('synced_users', 0)
            print(f"📊 Users synced: {synced_users}")
            
            # Check sync service status
            print(f"\n📋 Sync service status:")
            print(f"  - Enabled: {triggered_sync_service.enabled}")
            print(f"  - Pending: {triggered_sync_service.pending}")
            print(f"  - Last sync: {triggered_sync_service.last_sync_time}")
            print(f"  - Cooldown remaining: {triggered_sync_service.get_cooldown_remaining()}s")
            
        else:
            print(f"❌ Sync failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Sync test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sync_for_user())