from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncio
import logging
from app.core.config import settings
from app.core.database import get_supabase

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token configuration
SECRET_KEY = getattr(settings, 'SECRET_KEY', 'your-secret-key-here-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES', 60)  # 1 hour default
REFRESH_TOKEN_EXPIRE_DAYS = getattr(settings, 'REFRESH_TOKEN_EXPIRE_DAYS', 7)  # 7 days default

# Security scheme
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

async def verify_password_async(plain_password: str, hashed_password: str) -> bool:
    """Async version of password verification to prevent blocking"""
    # Move CPU-intensive bcrypt verification to thread pool
    return await asyncio.to_thread(pwd_context.verify, plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

async def get_password_hash_async(password: str) -> str:
    """Async version of password hashing to prevent blocking"""
    # Move CPU-intensive bcrypt hashing to thread pool
    return await asyncio.to_thread(pwd_context.hash, password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(user_id: str) -> str:
    """Create a refresh token and store it in database"""
    # Generate a random refresh token
    import secrets
    refresh_token = secrets.token_urlsafe(32)
    
    # Hash the token for storage
    token_hash = pwd_context.hash(refresh_token)
    
    # Calculate expiration
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Store in database
    supabase = get_supabase()
    try:
        supabase.table('refresh_tokens').insert({
            'user_id': user_id,
            'token_hash': token_hash,
            'expires_at': expires_at.isoformat()
        }).execute()
        
        return refresh_token
    except Exception as e:
        logger.error(f"Error storing refresh token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create refresh token"
        )

async def verify_refresh_token(refresh_token: str) -> Optional[dict]:
    """Verify a refresh token and return user info - optimized for performance"""
    supabase = get_supabase()
    try:
        # Get all refresh tokens (we need to check all since we don't know the user_id)
        result = await asyncio.to_thread(
            lambda: supabase.table('refresh_tokens').select('*').execute()
        )
        
        for token_record in result.data:
            try:
                # Check if token matches and is valid
                token_matches = await asyncio.to_thread(
                    pwd_context.verify, refresh_token, token_record['token_hash']
                )
                
                if token_matches:
                    # Check if revoked
                    if token_record['is_revoked']:
                        continue
                    
                    # Check expiration - handle different datetime formats
                    expires_at = token_record['expires_at']
                    now = datetime.utcnow()
                    
                    if isinstance(expires_at, str):
                        # Remove timezone info for comparison
                        if 'T' in expires_at:
                            expires_at = expires_at.split('T')[0] + ' ' + expires_at.split('T')[1]
                        if expires_at.endswith('Z'):
                            expires_at = expires_at[:-1]
                        if '+' in expires_at:
                            expires_at = expires_at.split('+')[0]
                        
                        try:
                            expires_datetime = datetime.fromisoformat(expires_at)
                        except:
                            # Try parsing as regular datetime
                            expires_datetime = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S')
                    else:
                        expires_datetime = expires_at
                    
                    if expires_datetime > now:
                        # Get user info
                        user_result = await asyncio.to_thread(
                            lambda: supabase.table('users').select('*').eq('id', token_record['user_id']).single().execute()
                        )
                        
                        if user_result.data and user_result.data.get('is_active', True):
                            return {
                                'user_id': token_record['user_id'],
                                'user': user_result.data
                            }
            except Exception as token_error:
                logger.error(f"Error processing token record: {token_error}")
                continue
        
        return None
    except Exception as e:
        logger.error(f"Error verifying refresh token: {e}")
        return None

async def revoke_refresh_token(refresh_token: str) -> bool:
    """Revoke a refresh token - optimized for performance and speed"""
    supabase = get_supabase()
    try:
        # OPTIMIZATION: Hash the token and try to find it directly
        # This is much faster than fetching all tokens
        token_hash = await asyncio.to_thread(pwd_context.hash, refresh_token)
        
        # Try to find the token by hash (if we stored it)
        # If not found, fall back to the old method but with timeout
        try:
            result = await asyncio.to_thread(
                lambda: supabase.table('refresh_tokens').select('*').eq('token_hash', token_hash).execute()
            )
            if result.data:
                # Found the token, revoke it
                await asyncio.to_thread(
                    lambda: supabase.table('refresh_tokens').update({
                        'is_revoked': True
                    }).eq('token_hash', token_hash).execute()
                )
                return True
        except Exception:
            pass
        
        # Fallback: try to find by verification (but with limit to avoid hanging)
        try:
            result = await asyncio.to_thread(
                lambda: supabase.table('refresh_tokens').select('*').limit(100).execute()
            )
            
            for token_record in result.data:
                token_matches = await asyncio.to_thread(
                    pwd_context.verify, refresh_token, token_record['token_hash']
                )
                
                if token_matches:
                    await asyncio.to_thread(
                        lambda: supabase.table('refresh_tokens').update({
                            'is_revoked': True
                        }).eq('id', token_record['id']).execute()
                    )
                    return True
        except Exception:
            pass
        
        return False
    except Exception as e:
        logger.error(f"Error revoking refresh token: {e}")
        return False

async def revoke_all_user_tokens(user_id: str) -> bool:
    """Revoke all refresh tokens for a user - optimized for performance"""
    supabase = get_supabase()
    try:
        await asyncio.to_thread(
            lambda: supabase.table('refresh_tokens').update({
                'is_revoked': True
            }).eq('user_id', user_id).execute()
        )
        return True
    except Exception as e:
        logger.error(f"Error revoking user tokens: {e}")
        return False

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return payload
    except JWTError:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user from JWT token - optimized for performance"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database using async to prevent blocking
    supabase = get_supabase()
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table('users').select('*').eq('id', user_id).single().execute()
        )
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = result.data
        if not user.get('is_active', True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Get current active user"""
    if not current_user.get('is_active', True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Authenticate a user with email and password - optimized for performance"""
    supabase = get_supabase()
    try:
        # Move database query to thread pool to prevent blocking
        result = await asyncio.to_thread(
            lambda: supabase.table('users').select('*').eq('email', email).single().execute()
        )
        
        if not result.data:
            # Still run password verification to prevent timing attacks
            await verify_password_async("dummy", "$2b$12$dummy.hash.to.prevent.timing.attacks")
            return None
        
        user = result.data
        
        # Use async password verification to prevent blocking
        password_valid = await verify_password_async(password, user['password_hash'])
        if not password_valid:
            return None
        
        return user
        
    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        return None

async def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email - optimized for performance"""
    supabase = get_supabase()
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table('users').select('*').eq('email', email).single().execute()
        )
        return result.data if result.data else None
    except Exception as e:
        logger.error(f"Error fetching user by email: {e}")
        return None

async def get_user_by_id(user_id: str) -> Optional[dict]:
    """Get user by ID - optimized for performance"""
    supabase = get_supabase()
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table('users').select('*').eq('id', user_id).single().execute()
        )
        return result.data if result.data else None
    except Exception as e:
        logger.error(f"Error fetching user by ID: {e}")
        return None

async def create_user(email: str, password: str, first_name: str, last_name: str) -> Optional[dict]:
    """Create a new user - optimized for performance"""
    supabase = get_supabase()
    try:
        # Check if user already exists
        existing_user = await get_user_by_email(email)
        if existing_user:
            return None
        
        # Hash password asynchronously to prevent blocking
        hashed_password = await get_password_hash_async(password)
        
        # Create user
        user_data = {
            'email': email,
            'password_hash': hashed_password,
            'first_name': first_name,
            'last_name': last_name,
            'is_active': True,
            'is_verified': False
        }
        
        result = await asyncio.to_thread(
            lambda: supabase.table('users').insert(user_data).execute()
        )
        
        if result.data:
            return result.data[0]
        
        return None
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None

async def update_user(user_id: str, update_data: dict) -> Optional[dict]:
    """Update user information"""
    supabase = get_supabase()
    try:
        # Remove sensitive fields that shouldn't be updated directly
        update_data.pop('password_hash', None)
        update_data.pop('id', None)
        update_data.pop('created_at', None)
        
        # Add updated_at timestamp
        update_data['updated_at'] = datetime.utcnow().isoformat()
        
        result = await asyncio.to_thread(
            lambda: supabase.table('users').update(update_data).eq('id', user_id).execute()
        )
        if result.data:
            return result.data[0]
        
        return None
        
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return None

async def delete_user(user_id: str) -> bool:
    """Delete a user account - optimized for performance"""
    supabase = get_supabase()
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table('users').delete().eq('id', user_id).execute()
        )
        return bool(result.data)
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return False

async def change_user_password(user_id: str, current_password: str, new_password: str) -> bool:
    """Change user password - optimized for performance"""
    try:
        # Get current user
        user = await get_user_by_id(user_id)
        if not user:
            return False
        
        # Verify current password asynchronously
        password_valid = await verify_password_async(current_password, user['password_hash'])
        if not password_valid:
            return False
        
        # Hash new password asynchronously
        new_password_hash = await get_password_hash_async(new_password)
        
        # Update password
        supabase = get_supabase()
        result = await asyncio.to_thread(
            lambda: supabase.table('users').update({
                'password_hash': new_password_hash,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', user_id).execute()
        )
        
        return bool(result.data)
        
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        return False 