"""
Sync Configuration
Easy configuration for Google Sheets sync intervals and behavior
"""

# Sync intervals (in seconds)
SYNC_INTERVALS = {
    'triggered_sync_cooldown': 30,   # Reduced from 300 to 30 seconds (30s between triggered syncs)
    'manual_sync_cooldown': 120,     # 2 minutes between manual syncs
    'background_sync_interval': 1800, # 30 minutes for background sync (if enabled)
}

# Sync behavior settings
SYNC_SETTINGS = {
    'enable_triggered_sync': True,    # Enable sync on user actions
    'enable_manual_sync': True,       # Enable manual sync endpoints
    'enable_background_sync': False,  # Enable continuous background sync
    'sync_on_profile_create': True,   # Sync when user profile is created
    'sync_on_profile_update': True,   # Sync when user profile is updated
    'sync_on_quiz_completion': True,  # Sync when quiz is completed
    'sync_on_chat_message': False,    # Sync on every chat message (can be expensive)
}

# Google Sheets settings
GOOGLE_SHEETS_SETTINGS = {
    'max_retry_attempts': 3,          # Max retry attempts for failed syncs
    'retry_delay_seconds': 5,         # Delay between retry attempts
    'timeout_seconds': 60,            # Increased from 15 to 60 seconds timeout
}

def get_sync_interval(interval_type: str) -> int:
    """Get sync interval by type"""
    return SYNC_INTERVALS.get(interval_type, 300)

def get_sync_setting(setting_name: str) -> bool:
    """Get sync setting by name"""
    return SYNC_SETTINGS.get(setting_name, True)

def get_google_sheets_setting(setting_name: str) -> int:
    """Get Google Sheets setting by name"""
    return GOOGLE_SHEETS_SETTINGS.get(setting_name, 30)