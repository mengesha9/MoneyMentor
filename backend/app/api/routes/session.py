from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from app.core.auth import get_current_active_user
from app.core.database import get_supabase
from app.utils.session import (
    get_all_user_sessions,
    get_recent_user_sessions,
    cleanup_empty_sessions,
    delete_session
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/analysis")
async def analyze_user_sessions(
    current_user: dict = Depends(get_current_active_user),
    hours: int = Query(24, description="Hours to look back for recent sessions")
) -> Dict[str, Any]:
    """Analyze user sessions and provide statistics"""
    try:
        user_id = current_user["id"]
        
        # Get all user sessions
        all_sessions = await get_all_user_sessions(user_id)
        recent_sessions = await get_recent_user_sessions(user_id, hours)
        
        # Calculate statistics
        total_sessions = len(all_sessions)
        recent_sessions_count = len(recent_sessions)
        
        empty_chat_sessions = sum(1 for s in all_sessions if not s.get("chat_history"))
        sessions_with_chat = total_sessions - empty_chat_sessions
        
        # Calculate average messages per session (for sessions with chat)
        total_messages = sum(len(s.get("chat_history", [])) for s in all_sessions)
        avg_messages = total_messages / sessions_with_chat if sessions_with_chat > 0 else 0
        
        # Find oldest and newest sessions
        if all_sessions:
            oldest_session = min(all_sessions, key=lambda x: x.get("created_at", ""))
            newest_session = max(all_sessions, key=lambda x: x.get("created_at", ""))
        else:
            oldest_session = newest_session = None
        
        return {
            "user_id": user_id,
            "total_sessions": total_sessions,
            "recent_sessions": recent_sessions_count,
            "empty_chat_sessions": empty_chat_sessions,
            "sessions_with_chat": sessions_with_chat,
            "empty_chat_percentage": round((empty_chat_sessions / total_sessions * 100) if total_sessions > 0 else 0, 2),
            "total_messages": total_messages,
            "average_messages_per_session": round(avg_messages, 2),
            "oldest_session": oldest_session.get("created_at") if oldest_session else None,
            "newest_session": newest_session.get("created_at") if newest_session else None,
            "analysis_hours": hours
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze user sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cleanup")
async def cleanup_user_sessions(
    current_user: dict = Depends(get_current_active_user),
    days_old: int = Query(30, description="Delete empty sessions older than this many days"),
    user_only: bool = Query(True, description="Clean up only current user's sessions")
) -> Dict[str, Any]:
    """Clean up empty sessions"""
    try:
        user_id = current_user["id"]
        
        if user_only:
            # Clean up only current user's sessions
            result = await cleanup_empty_sessions(user_id, days_old)
        else:
            # Clean up all users' sessions (admin only)
            result = await cleanup_empty_sessions(None, days_old)
        
        return {
            "success": True,
            "message": f"Cleanup completed successfully",
            "deleted_count": result["deleted_count"],
            "cutoff_date": result.get("cutoff_date"),
            "user_id": user_id if user_only else "all_users"
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{session_id}")
async def delete_user_session(
    session_id: str,
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Delete a specific session"""
    try:
        user_id = current_user["id"]
        
        # Verify the session belongs to the current user
        user_sessions = await get_all_user_sessions(user_id)
        session_exists = any(s["session_id"] == session_id for s in user_sessions)
        
        if not session_exists:
            raise HTTPException(status_code=404, detail="Session not found or access denied")
        
        # Delete the session
        success = await delete_session(session_id)
        
        if success:
            return {
                "success": True,
                "message": f"Session {session_id} deleted successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete session")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent")
async def get_recent_sessions(
    current_user: dict = Depends(get_current_active_user),
    hours: int = Query(24, description="Hours to look back")
) -> Dict[str, Any]:
    """Get recent sessions for the current user"""
    try:
        user_id = current_user["id"]
        recent_sessions = await get_recent_user_sessions(user_id, hours)
        
        return {
            "user_id": user_id,
            "recent_sessions": recent_sessions,
            "count": len(recent_sessions),
            "hours_back": hours
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 