# Google Sheets Sync Approach

## Overview

The Google Sheets sync uses the existing background sync service that was already working, but triggers it on-demand after quiz submissions. This prevents API blocking while ensuring data is synced to the correct Google Sheets tabs.

## How It Works

### 1. Quiz Submission Triggers
Google Sheets sync now happens automatically after:
- **Quiz submissions** (`/api/quiz/submit`)
- **Course quiz submissions** (`/api/course/quiz/submit`) 
- **Course completions** (`/api/course/complete`)

### 2. What Gets Synced
After each quiz submission, the system:
1. **Triggers the existing background sync service** asynchronously
2. **Updates course statistics** in the database (handled by background service)
3. **Syncs to existing Google Sheets tabs** (using the proven sync logic)
4. **Logs individual quiz responses** to Google Sheets (existing functionality)

### 3. Benefits
- ✅ **No API blocking** - sync happens asynchronously after response is sent
- ✅ **Uses proven sync logic** - leverages existing background sync service
- ✅ **Syncs to correct tabs** - uses the already configured Google Sheets tabs
- ✅ **Non-blocking** - quiz submission doesn't wait for sync to complete
- ✅ **Reliable** - uses the same retry logic and error handling

## Manual Operations

### Session Cleanup
Run session cleanup manually when needed:
```bash
python run_session_cleanup.py
```

### Force Sync
Use the existing sync endpoints:
- `GET /api/sync/status` - Check sync status
- `POST /api/sync/force` - Force immediate sync

## Environment Configuration

### Development
- Sync happens immediately after quiz submissions
- Individual quiz responses are logged to Google Sheets
- Course statistics are updated and synced

### Production
- Same behavior as development
- No background services running
- All sync happens on-demand

## Monitoring

Check the logs for sync activities:
- `Background sync triggered for user {user_id} after quiz submission`
- `Forcing immediate sync to Google Sheets`
- `Background sync successful: {count} user profiles synced to Google Sheets`
- `Failed to trigger background sync after quiz submission` (warnings)

## Troubleshooting

If sync fails:
1. Check Google Sheets API credentials
2. Verify spreadsheet permissions
3. Check logs for specific error messages
4. Use manual sync endpoints to test

The sync failure won't block the quiz submission - it's designed to be non-blocking. 