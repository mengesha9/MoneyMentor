import re
import logging
from typing import Optional
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

def is_valid_uuid(user_id: str) -> bool:
    """Check if user_id is a valid UUID format"""
    if not user_id or not isinstance(user_id, str):
        return False
    
    # UUID pattern: 8-4-4-4-12 hexadecimal characters
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    return bool(uuid_pattern.match(user_id))

def validate_user_id(user_id: str, context: str = "database operation") -> str:
    """
    Validate user_id and ensure it's a proper UUID from authentication token
    
    Args:
        user_id: The user ID to validate
        context: Context for error messages
    
    Returns:
        The validated user_id
        
    Raises:
        HTTPException: If user_id is invalid
    """
    if not user_id:
        logger.error(f"❌ {context}: user_id is None or empty")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user_id: user_id is required for {context}"
        )
    
    if not isinstance(user_id, str):
        logger.error(f"❌ {context}: user_id is not a string: {type(user_id)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user_id: user_id must be a string for {context}"
        )
    
    # Check for common fake user ID patterns
    fake_patterns = [
        r'^default_user$',
        r'^perf_user_\d+$',
        r'^test_user_\d+$',
        r'^user_sessions_user_\d+$',
        r'^fake_user_\d+$',
        r'^demo_user_\d+$',
        r'^temp_user_\d+$',
        r'^anonymous_\d+$',
        r'^guest_\d+$',
        r'^mock_user_\d+$',
        r'^sample_user_\d+$',
        r'^dummy_user_\d+$'
    ]
    
    for pattern in fake_patterns:
        if re.match(pattern, user_id, re.IGNORECASE):
            logger.error(f"❌ {context}: Detected fake user_id pattern: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user_id: Fake user_id detected for {context}"
            )
    
    # Check if it's a valid UUID
    if not is_valid_uuid(user_id):
        logger.error(f"❌ {context}: user_id is not a valid UUID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user_id: user_id must be a valid UUID for {context}"
        )
    
    logger.debug(f"✅ {context}: Validated user_id: {user_id}")
    return user_id

def require_authenticated_user_id(user_id: Optional[str], context: str = "database operation") -> str:
    """
    Require a user_id from authentication token (no defaults allowed)
    
    Args:
        user_id: The user ID from authentication token
        context: Context for error messages
    
    Returns:
        The validated user_id
        
    Raises:
        HTTPException: If user_id is missing or invalid
    """
    if user_id is None:
        logger.error(f"❌ {context}: user_id is None - authentication required")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication required: user_id must be provided from token for {context}"
        )
    
    return validate_user_id(user_id, context)

def sanitize_user_id_for_logging(user_id: str) -> str:
    """Sanitize user_id for safe logging (show only first 8 characters)"""
    if not user_id or len(user_id) < 8:
        return "***"
    return f"{user_id[:8]}..." 