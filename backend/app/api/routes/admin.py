"""
Admin API Routes
Provides endpoints for managing sync configuration and system settings
"""

from fastapi import APIRouter, HTTPException, status, Depends
from app.core.auth import get_current_active_user
from app.config.sync_config import SYNC_INTERVALS, SYNC_SETTINGS, GOOGLE_SHEETS_SETTINGS
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/sync/config")
async def get_sync_config(
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get current sync configuration
    
    Returns:
        Current sync configuration
    """
    try:
        # Import services locally to avoid circular imports
        from app.services.triggered_sync_service import triggered_sync_service
        from app.services.manual_sync_service import manual_sync_service
        
        return {
            'intervals': SYNC_INTERVALS,
            'settings': SYNC_SETTINGS,
            'google_sheets': GOOGLE_SHEETS_SETTINGS,
            'triggered_sync_status': triggered_sync_service.get_sync_status(),
            'manual_sync_status': manual_sync_service.get_sync_status()
        }
        
    except Exception as e:
        logger.error(f"❌ Get sync config error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync config: {str(e)}"
        )

@router.post("/sync/config/interval/{interval_type}")
async def update_sync_interval(
    interval_type: str,
    seconds: int,
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Update sync interval
    
    Args:
        interval_type: Type of interval to update (triggered_sync_cooldown, manual_sync_cooldown, etc.)
        seconds: New interval in seconds
        
    Returns:
        Updated configuration
    """
    try:
        if interval_type not in SYNC_INTERVALS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid interval type. Valid types: {list(SYNC_INTERVALS.keys())}"
            )
        
        if seconds < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Interval must be at least 10 seconds"
            )
        
        # Update the configuration
        SYNC_INTERVALS[interval_type] = seconds
        
        # Update the triggered sync service if it's the cooldown
        if interval_type == 'triggered_sync_cooldown':
            from app.services.triggered_sync_service import triggered_sync_service
            triggered_sync_service.set_sync_cooldown(seconds)
        
        logger.info(f"⏰ Sync interval updated: {interval_type} = {seconds} seconds by user {current_user['id']}")
        
        return {
            'success': True,
            'message': f'Updated {interval_type} to {seconds} seconds',
            'interval_type': interval_type,
            'seconds': seconds
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Update sync interval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update sync interval: {str(e)}"
        )

@router.post("/sync/trigger")
async def trigger_manual_sync(
    force: bool = False,
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Manually trigger a sync to Google Sheets
    
    Args:
        force: If True, sync even if recently synced
        
    Returns:
        Sync results
    """
    try:
        # Import service locally to avoid circular imports
        from app.services.manual_sync_service import manual_sync_service
        
        logger.info(f"🔄 Manual sync triggered by user {current_user['id']} (force={force})")
        
        result = await manual_sync_service.sync_user_profiles_to_sheets(force_sync=force)
        
        if result['success']:
            logger.info(f"✅ Manual sync completed successfully")
        else:
            logger.warning(f"⚠️ Manual sync failed: {result['message']}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Manual sync trigger error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger sync: {str(e)}"
        )

@router.get("/sync/stats")
async def get_sync_stats(
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get sync statistics and status
    
    Returns:
        Sync statistics
    """
    try:
        # Import services locally to avoid circular imports
        from app.services.triggered_sync_service import triggered_sync_service
        from app.services.manual_sync_service import manual_sync_service
        
        triggered_status = triggered_sync_service.get_sync_status()
        manual_status = manual_sync_service.get_sync_status()
        
        return {
            'triggered_sync': triggered_status,
            'manual_sync': manual_status,
            'config': {
                'intervals': SYNC_INTERVALS,
                'settings': SYNC_SETTINGS
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Get sync stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync stats: {str(e)}"
        )