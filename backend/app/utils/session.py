from datetime import datetime, timedelta
import json
import uuid
from typing import Dict, Any, Optional, List
from app.core.database import get_supabase, supabase
from app.utils.user_validation import require_authenticated_user_id, sanitize_user_id_for_logging
import logging
import asyncio
from functools import lru_cache

from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory session cache for faster access
_session_cache = {}
_cache_lock = asyncio.Lock()

async def create_session(session_id: str = None, user_id: str = None, initial_chat_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a new session with caching - requires authenticated user_id"""
    try:
        # Validate user_id is provided and is a real UUID from authentication
        validated_user_id = require_authenticated_user_id(user_id, "session creation")
        sanitized_user_id = sanitize_user_id_for_logging(validated_user_id)
        
        logger.debug(f"Creating session with session_id: {session_id}, user_id: {sanitized_user_id}")
        
        # Validate session_id if provided
        if session_id and (session_id.startswith('{') or session_id.startswith('[')):
            logger.error(f"Invalid session_id format - looks like JSON: {session_id}")
            raise ValueError(f"Invalid session_id format: {session_id}")
        
        # Check if user already has recent sessions to avoid creating unnecessary ones
        recent_sessions = await get_recent_user_sessions(validated_user_id, hours=1)
        if recent_sessions and len(recent_sessions) >= 3:
            logger.warning(f"User {sanitized_user_id} has {len(recent_sessions)} recent sessions, consider reusing existing")
        
        # Use provided chat history or start with empty array
        chat_history = initial_chat_history if initial_chat_history is not None else []
        
        # Store in the correct format matching actual database schema
        db_session_data = {
            "session_id": session_id,  # Use the provided session_id
            "user_id": validated_user_id,
            "chat_history": chat_history,  # Use provided chat history instead of empty array
            "progress": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert into database and get the generated id
        logger.debug(f"Inserting session data: {db_session_data}")
        try:
            result = supabase.table("user_sessions").insert(db_session_data).execute()
            logger.debug(f"Insert result: {result}")
        except Exception as insert_error:
            logger.error(f"Database insert failed: {insert_error}")
            logger.error(f"Insert data was: {db_session_data}")
            raise
        
        if not result.data:
            raise Exception("Failed to create session in database")
        
        # Get the created session with generated id
        created_session = result.data[0]
        logger.debug(f"Created session in database: {created_session}")
        
        # Use the provided session_id as the primary identifier
        actual_session_id = session_id if session_id else str(created_session["id"])
        
        # Create session data in expected format
        session_data = {
            "session_id": actual_session_id,  # Use provided session_id or database id as fallback
            "user_id": user_id,
            "chat_history": chat_history,  # Use the same chat history
            "quiz_history": [],
            "progress": {},
            "created_at": created_session["created_at"],
            "updated_at": created_session["updated_at"]
        }
        
        # Store in cache immediately
        async with _cache_lock:
            _session_cache[actual_session_id] = session_data
        
        logger.info(f"Session created and stored in database: {actual_session_id} with {len(chat_history)} initial messages")
        return session_data
        
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise

async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session by ID with caching"""
    try:
        session_id_str = str(session_id)
        # Check cache first
        async with _cache_lock:
            if session_id_str in _session_cache:
                return _session_cache[session_id_str]
        # If not in cache, get from database using session_id column first, then id column as fallback
        result = supabase.table("user_sessions").select("*").eq("session_id", session_id_str).execute()
        logger.debug(f"Supabase query by session_id={session_id_str} result: {result.data}")
        if not result.data or len(result.data) == 0:
            # Fallback to searching by id column (for backward compatibility)
            import re
            uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
            if uuid_pattern.match(session_id_str):
                result = supabase.table("user_sessions").select("*").eq("id", session_id_str).execute()
                logger.debug(f"Supabase query by id={session_id_str} result: {result.data}")
                if result.data and len(result.data) > 0:
                    logger.info(f"Found session using id column fallback for UUID session_id: {session_id_str}")
            else:
                logger.debug(f"Session not found and session_id '{session_id_str}' is not a UUID, skipping id column fallback")
        if result.data and len(result.data) > 0:
            db_data = result.data[0]
            session_data = {
                "session_id": db_data.get("session_id") or str(db_data["id"]),
                "user_id": db_data.get("user_id"),
                "chat_history": db_data.get("chat_history", []),
                "progress": db_data.get("progress", {}),
                "created_at": db_data.get("created_at"),
                "updated_at": db_data.get("updated_at")
            }
            async with _cache_lock:
                _session_cache[session_id_str] = session_data
            return session_data
        return None
    except Exception as e:
        logger.error(f"Failed to get session: {e}")
        return None

async def update_session(session_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update session data with caching"""
    try:
        data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update cache immediately
        async with _cache_lock:
            if session_id in _session_cache:
                _session_cache[session_id].update(data)
                updated_session = _session_cache[session_id]
            else:
                # If not in cache, get from database first using session_id column, then id column as fallback
                result = supabase.table("user_sessions").select("*").eq("session_id", session_id).execute()
                
                if not result.data or len(result.data) == 0:
                    # Fallback to searching by id column (for backward compatibility)
                    # BUT only if the session_id looks like a UUID (to avoid false matches)
                    import re
                    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
                    
                    if uuid_pattern.match(session_id):
                        result = supabase.table("user_sessions").select("*").eq("id", session_id).execute()
                        if result.data and len(result.data) > 0:
                            logger.info(f"Found session using id column fallback for UUID session_id: {session_id}")
                    else:
                        logger.debug(f"Session not found and session_id '{session_id}' is not a UUID, skipping id column fallback")
                
                if result.data and len(result.data) > 0:
                    db_data = result.data[0]
                    # Convert database format to session format
                    session_data = {
                        "session_id": db_data.get("session_id") or str(db_data["id"]),  # Use session_id if available, otherwise database id
                        "user_id": db_data.get("user_id"),
                        "chat_history": db_data.get("chat_history", []),
                        "progress": db_data.get("progress", {}),
                        "created_at": db_data.get("created_at"),
                        "updated_at": db_data.get("updated_at")
                    }
                    session_data.update(data)
                    _session_cache[session_id] = session_data
                    updated_session = session_data
                else:
                    raise ValueError(f"Session {session_id} not found")
        
        # Async database update (fire-and-forget)
        asyncio.create_task(_update_session_async(session_id, data))
        
        return updated_session
        
    except Exception as e:
        logger.error(f"Failed to update session: {e}")
        raise

async def _update_session_async(session_id: str, data: Dict[str, Any]):
    """Update session in database asynchronously"""
    try:
        # Update the session using session_id column first, then id column as fallback
        update_data = {
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Map the data to the correct database columns
        if "chat_history" in data:
            update_data["chat_history"] = data["chat_history"]
        if "progress" in data:
            update_data["progress"] = data["progress"]
        
        # Try to update using session_id first
        result = supabase.table("user_sessions").update(update_data).eq("session_id", session_id).execute()
        
        # If no rows were updated, try using id column as fallback
        # BUT only if the session_id looks like a UUID (to avoid false matches)
        if not result.data or len(result.data) == 0:
            import re
            uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
            
            # Only use id column fallback if session_id is actually a UUID
            if uuid_pattern.match(session_id):
                result = supabase.table("user_sessions").update(update_data).eq("id", session_id).execute()
                if result.data and len(result.data) > 0:
                    logger.info(f"Updated session using id column fallback for UUID session_id: {session_id}")
            else:
                logger.warning(f"Session not found and session_id '{session_id}' is not a UUID, skipping id column fallback")
            
    except Exception as e:
        logger.warning(f"Failed to update session in database: {e}")

async def _store_session_async(session_data: Dict[str, Any]):
    """Store session in database asynchronously"""
    try:
        # Store in the correct format matching actual database schema
        # Validate user_id is provided and is a real UUID
        user_id = session_data.get("user_id")
        validated_user_id = require_authenticated_user_id(user_id, "async session storage")
        
        db_session_data = {
            "session_id": session_data.get("session_id"),  # Include session_id if provided
            "user_id": validated_user_id,
            "chat_history": session_data.get("chat_history", []),
            "progress": session_data.get("progress", {}),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        supabase.table("user_sessions").insert(db_session_data).execute()
    except Exception as e:
        logger.warning(f"Failed to store session in database: {e}")

async def delete_session(session_id: str) -> bool:
    """Delete session with cache cleanup"""
    try:
        # Remove from cache
        async with _cache_lock:
            _session_cache.pop(session_id, None)
        
        # Delete from database using session_id column first, then id column as fallback
        result = supabase.table("user_sessions").delete().eq("session_id", session_id).execute()
        
        # If no rows were deleted, try using id column as fallback
        # BUT only if the session_id looks like a UUID (to avoid false matches)
        if not result.data or len(result.data) == 0:
            import re
            uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
            
            if uuid_pattern.match(session_id):
                result = supabase.table("user_sessions").delete().eq("id", session_id).execute()
                if result.data and len(result.data) > 0:
                    logger.info(f"Deleted session using id column fallback for UUID session_id: {session_id}")
            else:
                logger.warning(f"Session not found for deletion and session_id '{session_id}' is not a UUID, skipping id column fallback")
            
        return bool(result.data)
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise

async def add_chat_message(session_id: str, message: Dict[str, Any]) -> None:
    """Add a message to chat history with optimized caching"""
    try:
        # Update cache directly if available
        async with _cache_lock:
            if session_id in _session_cache:
                chat_history = _session_cache[session_id].get("chat_history", [])
                chat_history.append(message)
                _session_cache[session_id]["chat_history"] = chat_history
                _session_cache[session_id]["updated_at"] = datetime.utcnow().isoformat()
                
                # Async database update
                asyncio.create_task(_update_session_async(session_id, {
                    "chat_history": chat_history,
                    "updated_at": _session_cache[session_id]["updated_at"]
                }))
                return
        
        # Fallback to database if not in cache
        session = await get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
            
        chat_history = session.get("chat_history", [])
        chat_history.append(message)
        
        await update_session(session_id, {"chat_history": chat_history})
        
    except Exception as e:
        logger.error(f"Failed to add chat message: {e}")
        raise

async def add_quiz_response(session_id: str, quiz_data: Dict[str, Any]) -> None:
    """Add a quiz response to centralized quiz_responses table"""
    try:
        # Get session to get user_id
        session = await get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        user_id = session.get("user_id")
        if not user_id:
            raise ValueError(f"Session {session_id} has no user_id")
        
        # Prepare quiz response data for centralized storage
        quiz_response_data = {
            'user_id': user_id,
            'quiz_id': quiz_data.get('quiz_id', f'micro_quiz_{session_id}_{datetime.utcnow().timestamp()}'),
            'topic': quiz_data.get('topic', 'General Finance'),
            'selected': quiz_data.get('selected_option', ''),
            'correct': quiz_data.get('correct', False),
            'quiz_type': 'micro',  # Session-specific quizzes are micro quizzes
            'score': 100.0 if quiz_data.get('correct', False) else 0.0,
            'session_id': session_id,
            'question_data': quiz_data.get('question_data', {}),
            'correct_answer': quiz_data.get('correct_answer', ''),
            'explanation': quiz_data.get('explanation', '')
        }
        
        # Save to centralized quiz_responses table
        from app.core.database import get_supabase
        supabase = get_supabase()
        supabase.table('quiz_responses').insert(quiz_response_data).execute()
        
        logger.info(f"Session quiz response saved to centralized quiz_responses for session {session_id}, user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to add quiz response to centralized storage: {e}")
        raise

async def update_progress(session_id: str, progress_data: Dict[str, Any]) -> None:
    """Update session progress with optimized caching"""
    try:
        # Update cache directly if available
        async with _cache_lock:
            if session_id in _session_cache:
                current_progress = _session_cache[session_id].get("progress", {})
                current_progress.update(progress_data)
                _session_cache[session_id]["progress"] = current_progress
                _session_cache[session_id]["updated_at"] = datetime.utcnow().isoformat()
                
                # Async database update
                asyncio.create_task(_update_session_async(session_id, {
                    "progress": current_progress,
                    "updated_at": _session_cache[session_id]["updated_at"]
                }))
                return
        
        # Fallback to database if not in cache
        session = await get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
            
        current_progress = session.get("progress", {})
        current_progress.update(progress_data)
        
        await update_session(session_id, {"progress": current_progress})
        
    except Exception as e:
        logger.error(f"Failed to update progress: {e}")
        raise

async def clear_session_cache():
    """Clear the session cache (useful for testing or memory management)"""
    async with _cache_lock:
        _session_cache.clear()

def get_cache_stats():
    """Get cache statistics for monitoring"""
    return {
        "cache_size": len(_session_cache),
        "cached_sessions": list(_session_cache.keys())
    } 

async def get_all_user_sessions(user_id: str) -> List[Dict[str, Any]]:
    """Get all sessions for a specific user"""
    try:
        # Validate user_id is a real UUID from authentication
        validated_user_id = require_authenticated_user_id(user_id, "get all user sessions")
        sanitized_user_id = sanitize_user_id_for_logging(validated_user_id)
        
        logger.debug(f"Getting all sessions for user: {sanitized_user_id}")
        
        # Get all sessions for the user from database
        result = supabase.table("user_sessions").select("*").eq("user_id", validated_user_id).order("updated_at", desc=True).execute()
        
        if not result.data:
            return []
        
        # Convert database format to expected session format
        sessions = []
        for db_data in result.data:
            session_data = {
                "session_id": db_data.get("session_id") or str(db_data["id"]),  # Use session_id if available, otherwise database id
                "user_id": db_data.get("user_id"),
                "chat_history": db_data.get("chat_history", []),
                "progress": db_data.get("progress", {}),
                "created_at": db_data.get("created_at"),
                "updated_at": db_data.get("updated_at"),
                "last_active": db_data.get("last_active")
            }
            sessions.append(session_data)
        
        logger.debug(f"Found {len(sessions)} sessions for user {sanitized_user_id}")
        return sessions
        
    except Exception as e:
        logger.error(f"Failed to get all user sessions: {e}")
        return [] 

async def get_recent_user_sessions(user_id: str, hours: int = 24) -> List[Dict[str, Any]]:
    """Get recent sessions for a user within specified hours"""
    try:
        # Validate user_id is a real UUID from authentication
        validated_user_id = require_authenticated_user_id(user_id, "get recent user sessions")
        sanitized_user_id = sanitize_user_id_for_logging(validated_user_id)
        
        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get recent sessions from database
        result = supabase.table("user_sessions").select("*").eq("user_id", validated_user_id).gte("created_at", cutoff_time.isoformat()).order("created_at", desc=True).execute()
        
        if not result.data:
            return []
        
        # Convert database format to expected session format
        sessions = []
        for db_data in result.data:
            session_data = {
                "session_id": db_data.get("session_id") or str(db_data["id"]),  # Use session_id if available, otherwise database id
                "user_id": db_data.get("user_id"),
                "chat_history": db_data.get("chat_history", []),
                "progress": db_data.get("progress", {}),
                "created_at": db_data.get("created_at"),
                "updated_at": db_data.get("updated_at"),
                "last_active": db_data.get("last_active")
            }
            sessions.append(session_data)
        
        return sessions
        
    except Exception as e:
        logger.error(f"Failed to get recent user sessions: {e}")
        return []

async def cleanup_empty_sessions(user_id: str = None, days_old: int = 30) -> Dict[str, Any]:
    """Clean up sessions with empty chat history older than specified days"""
    try:
        cutoff_time = datetime.utcnow() - timedelta(days=days_old)
        
        if user_id:
            # Clean up for specific user
            validated_user_id = require_authenticated_user_id(user_id, "cleanup empty sessions")
            result = supabase.table("user_sessions").delete().eq("user_id", validated_user_id).lt("created_at", cutoff_time.isoformat()).eq("chat_history", []).execute()
        else:
            # Clean up for all users
            result = supabase.table("user_sessions").delete().lt("created_at", cutoff_time.isoformat()).eq("chat_history", []).execute()
        
        deleted_count = len(result.data) if result.data else 0
        
        # Clear cache for deleted sessions
        if result.data:
            async with _cache_lock:
                for session_data in result.data:
                    session_id = str(session_data.get("id"))
                    _session_cache.pop(session_id, None)
        
        logger.info(f"Cleaned up {deleted_count} empty sessions older than {days_old} days")
        return {
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_time.isoformat(),
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup empty sessions: {e}")
        return {
            "deleted_count": 0,
            "error": str(e)
        } 