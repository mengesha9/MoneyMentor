from app.services.triggered_sync_service import triggered_sync_service
from app.config.sync_config import get_sync_setting, get_sync_interval
from app.services.google_sheets_service import GoogleSheetsService
import logging
import asyncio

logging.basicConfig(level=logging.INFO)

async def test_sync():
    print('=== SYNC CONFIGURATION ===')
    print(f'Triggered sync enabled: {get_sync_setting("enable_triggered_sync")}')
    print(f'Sync on profile create: {get_sync_setting("sync_on_profile_create")}')
    print(f'Triggered sync cooldown: {get_sync_interval("triggered_sync_cooldown")} seconds')

    print('\n=== SYNC STATUS ===')
    status = triggered_sync_service.get_sync_status()
    for key, value in status.items():
        print(f'{key}: {value}')

    print('\n=== GOOGLE SHEETS SERVICE TEST ===')
    try:
        sheets_service = GoogleSheetsService()
        connection_test = sheets_service.test_connection()
        print(f'Google Sheets connection: {connection_test}')
        
        sheet_info = sheets_service.get_sheet_info()
        if sheet_info:
            print(f'Sheet title: {sheet_info.get("title", "Unknown")}')
            print(f'Available tabs: {sheet_info.get("sheets", [])}')
        else:
            print('Could not get sheet info')
    except Exception as e:
        print(f'Google Sheets service error: {e}')

    print('\n=== TESTING SYNC TRIGGER ===')
    result = triggered_sync_service.trigger_sync('test_sync')
    print(f'Sync trigger result: {result}')
    
    # Wait a bit to see if sync completes
    await asyncio.sleep(2)
    
    print('\n=== SYNC STATUS AFTER TRIGGER ===')
    status = triggered_sync_service.get_sync_status()
    for key, value in status.items():
        print(f'{key}: {value}')

if __name__ == "__main__":
    asyncio.run(test_sync())