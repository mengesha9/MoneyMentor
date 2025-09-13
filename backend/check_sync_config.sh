#!/bin/bash

# Simple test to check sync configuration and timing
# Run with: bash check_sync_config.sh

echo "=== SYNC CONFIGURATION CHECK ==="
echo

# Activate virtual environment
source source/Scripts/activate

# Check sync configuration
python -c "
import sys
import os
sys.path.append('app')

from app.config.sync_config import get_sync_interval, get_sync_setting

print('=== SYNC SETTINGS ===')
print(f'Triggered sync enabled: {get_sync_setting(\"enable_triggered_sync\")}')
print(f'Sync on profile create: {get_sync_setting(\"sync_on_profile_create\")}')
print(f'Triggered sync cooldown: {get_sync_interval(\"triggered_sync_cooldown\")} seconds')
print(f'Manual sync cooldown: {get_sync_interval(\"manual_sync_cooldown\")} seconds')
print()

print('=== TIMING EXPECTATIONS ===')
cooldown = get_sync_interval('triggered_sync_cooldown')
if cooldown <= 60:
    print(f'✅ Good: Short cooldown ({cooldown}s) - users appear quickly')
else:
    print(f'⚠️  Long cooldown ({cooldown}s) - users may wait up to {cooldown/60:.1f} minutes')

print()
print('Expected timeline after registration:')
print('1. Registration response: 1-2 seconds')
print('2. Background sync trigger: +1-3 seconds')
print('3. Google Sheets API call: +5-15 seconds')
print('4. Total time to sheets: ~7-20 seconds (if no cooldown)')
print(f'5. With cooldown delay: up to {cooldown} seconds')
"

echo
echo "=== TEST GOOGLE SHEETS CONNECTION ==="

# Quick connection test
python -c "
import sys
import os
sys.path.append('app')

try:
    from app.services.google_sheets_service import GoogleSheetsService
    
    print('Testing Google Sheets connection...')
    sheets = GoogleSheetsService()
    
    if sheets.service and sheets.spreadsheet_id:
        print('✅ Google Sheets service initialized')
        print(f'Spreadsheet ID: {sheets.spreadsheet_id[:20]}...')
        
        # Test connection
        info = sheets.get_sheet_info()
        if info:
            print(f'Sheet title: {info.get(\"title\", \"Unknown\")}')
            print(f'Available tabs: {info.get(\"sheets\", [])}')
            
            # Check if UserProfiles tab exists
            tabs = info.get('sheets', [])
            if 'UserProfiles' in tabs:
                print('✅ UserProfiles tab exists')
            else:
                print('⚠️  UserProfiles tab missing - this will cause sync failures')
        else:
            print('❌ Could not get sheet info')
    else:
        print('❌ Google Sheets service not properly configured')
        
except Exception as e:
    print(f'❌ Error: {e}')
"