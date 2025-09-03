import Cookies from 'js-cookie';
import { refreshToken } from './chatWidget/api';

export interface SessionInfo {
  token: string;
  refreshToken: string;
  userId: string;
  expiresAt: Date | null;
  isExpired: boolean;
  timeUntilExpiry: number; // in milliseconds
}

/**
 * Get session information including expiration details
 */
export const getSessionInfo = (): SessionInfo | null => {
  const token = Cookies.get('auth_token');
  const refreshToken = Cookies.get('refresh_token');
  const userId = localStorage.getItem('moneymentor_user_id');
  
  if (!token || !refreshToken || !userId) return null;

  // For now, we'll use a simpler approach since js-cookie doesn't expose expiration easily
  // We'll store the expiration time in localStorage when setting the cookie
  const storedExpiresAt = localStorage.getItem('auth_token_expires');
  
  let expiresAt: Date | null = null;
  let isExpired = false;
  let timeUntilExpiry = 0;

  if (storedExpiresAt) {
    expiresAt = new Date(storedExpiresAt);
    const now = new Date();
    timeUntilExpiry = expiresAt.getTime() - now.getTime();
    isExpired = timeUntilExpiry <= 0;
  }

  return {
    token,
    refreshToken,
    userId,
    expiresAt,
    isExpired,
    timeUntilExpiry
  };
};

/**
 * Check if session is expired or will expire soon (within 5 minutes for 60-minute sessions)
 */
export const isSessionExpiredOrExpiringSoon = (): boolean => {
  const sessionInfo = getSessionInfo();
  if (!sessionInfo) return true;

  // Consider expired if:
  // 1. Session is already expired
  // 2. Session will expire within 5 minutes (appropriate for 60-minute sessions)
  const fiveMinutes = 5 * 60 * 1000;
  return sessionInfo.isExpired || sessionInfo.timeUntilExpiry <= fiveMinutes;
};

/**
 * Refresh the access token using the refresh token
 */
export const refreshAccessToken = async (): Promise<boolean> => {
  try {
    const refreshTokenValue = Cookies.get('refresh_token');
    if (!refreshTokenValue) {
      return false;
    }

    const result = await refreshToken(refreshTokenValue);

    if (result && result.access_token && result.refresh_token) {
      // Store new tokens - match backend configuration
      Cookies.set('auth_token', result.access_token, { expires: 1/24 }); // 60 minutes (1/24 days)
      Cookies.set('refresh_token', result.refresh_token, { expires: 7 }); // 7 days for refresh token
      
      // Update expiration time - 60 minutes
      const expiresAt = new Date(Date.now() + 60 * 60 * 1000); // 60 minutes
      localStorage.setItem('auth_token_expires', expiresAt.toISOString());
      
      return true;
    }
    
    return false;
  } catch (error) {
    console.error('Failed to refresh token:', error);
    return false;
  }
};

/**
 * Extend session with new expiration (legacy function - now uses refresh tokens)
 */
export const extendSession = async (keepLoggedIn: boolean = true): Promise<boolean> => {
  // Instead of just extending expiry, try to refresh the token
  return await refreshAccessToken();
};

/**
 * Clear session
 */
export const clearSession = (): void => {
  Cookies.remove('auth_token');
  Cookies.remove('refresh_token');
  localStorage.removeItem('auth_token_expires');
  localStorage.removeItem('moneymentor_user_id');
  localStorage.removeItem('moneymentor_user_name');
};

/**
 * Store authentication data from login/register response
 */
export const storeAuthData = (authData: any): void => {
  if (authData.access_token && authData.refresh_token && authData.user?.id) {
    // Store tokens - match backend configuration
    Cookies.set('auth_token', authData.access_token, { expires: 1/24 }); // 60 minutes (1/24 days)
    Cookies.set('refresh_token', authData.refresh_token, { expires: 7 }); // 7 days for refresh token
    
    // Store user ID from backend
    localStorage.setItem('moneymentor_user_id', authData.user.id);
    
    // Store expiration time - 60 minutes
    const expiresAt = new Date(Date.now() + 60 * 60 * 1000); // 60 minutes
    localStorage.setItem('auth_token_expires', expiresAt.toISOString());

    // Store user name for profile persistence
    if (authData.user.first_name || authData.user.last_name) {
      const fullName = `${authData.user.first_name || ''} ${authData.user.last_name || ''}`.trim();
      localStorage.setItem('moneymentor_user_name', fullName);
    }
  }
};

export const getStoredUserName = (): string | null => {
  return localStorage.getItem('moneymentor_user_name');
}; 