"""
Sync API Routes
Provides endpoints for manual Google Sheets sync
"""

from fastapi import APIRouter, HTTPException, status, Depends
from app.core.auth import get_current_active_user
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/sync/all")
async def sync_all_profiles(
    force: bool = False,
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Manually sync all user profiles to Google Sheets
    
    Args:
        force: If True, sync even if recently synced
        
    Returns:
        Sync results and statistics
    """
    try:
        # Import service locally to avoid circular imports
        from app.services.manual_sync_service import manual_sync_service
        
        logger.info(f"🔄 Manual sync requested by user {current_user['id']} (force={force})")
        
        result = await manual_sync_service.sync_user_profiles_to_sheets(force_sync=force)
        
        if result['success']:
            logger.info(f"✅ Manual sync completed successfully")
        else:
            logger.warning(f"⚠️ Manual sync failed: {result['message']}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Manual sync endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )

@router.post("/sync/user/{user_id}")
async def sync_single_user(
    user_id: str,
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Manually sync a specific user profile to Google Sheets
    
    Args:
        user_id: ID of the user to sync
        
    Returns:
        Sync results
    """
    try:
        # Import service locally to avoid circular imports
        from app.services.manual_sync_service import manual_sync_service
        
        logger.info(f"🔄 Single user sync requested for {user_id} by user {current_user['id']}")
        
        result = await manual_sync_service.sync_single_user_profile(user_id)
        
        if result['success']:
            logger.info(f"✅ Single user sync completed for {user_id}")
        else:
            logger.warning(f"⚠️ Single user sync failed for {user_id}: {result['message']}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Single user sync endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )

@router.get("/sync/status")
async def get_sync_status(
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get current sync status and statistics
    
    Returns:
        Sync status and statistics
    """
    try:
        # Import service locally to avoid circular imports
        from app.services.manual_sync_service import manual_sync_service
        
        status = manual_sync_service.get_sync_status()
        return status
        
    except Exception as e:
        logger.error(f"❌ Get sync status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync status: {str(e)}"
        )

@router.get("/sync/available")
async def is_sync_available(
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Check if sync is available (not in progress and not too recent)
    
    Returns:
        Whether sync is available
    """
    try:
        # Import service locally to avoid circular imports
        from app.services.manual_sync_service import manual_sync_service
        
        available = manual_sync_service.is_sync_available()
        return {
            'available': available,
            'message': 'Sync is available' if available else 'Sync is not available (in progress or too recent)'
        }
        
    except Exception as e:
        logger.error(f"❌ Check sync availability error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check sync availability: {str(e)}"
        )