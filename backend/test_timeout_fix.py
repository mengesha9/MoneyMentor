#!/usr/bin/env python3
"""
Test sync with increased timeout settings
"""

import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

async def test_sync_with_timeouts():
    """Test sync with increased timeout settings"""
    
    from app.services.manual_sync_service import ManualSyncService
    from app.services.triggered_sync_service import triggered_sync_service
    
    print("=== TESTING SYNC WITH INCREASED TIMEOUTS ===")
    
    # Test the user that had the timeout issue
    user_id = '66282ed0-2188-410e-82cd-2e038c3b88b8'
    print(f"Testing sync for user: {user_id}")
    
    try:
        manual_sync = ManualSyncService()
        result = await manual_sync.sync_specific_user_profiles_to_sheets([user_id], force_sync=True)
        
        if result.get('success'):
            print(f"✅ Sync successful: {result.get('message', 'No message')}")
            print(f"📊 Users synced: {result.get('synced_users', 0)}")
            
            # Update the triggered sync service timestamp
            triggered_sync_service.last_sync_time = asyncio.get_event_loop().time()
            print("✅ Sync service timestamp updated")
            
        else:
            print(f"❌ Sync failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sync_with_timeouts())