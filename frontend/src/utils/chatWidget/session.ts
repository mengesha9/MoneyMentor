import { v4 as uuidv4 } from 'uuid';
import { STORAGE_KEYS } from '../../types';
import Cookies from 'js-cookie';


// Helper to get token from cookies
const getAuthToken = () => Cookies.get('auth_token');

// Helper to add Authorization header if token exists
const withAuth = (headers: Record<string, string> = {}) => {
  const token = getAuthToken();
  return token ? { ...headers, Authorization: `Bearer ${token}` } : headers;
};

export interface SessionIds {
  userId: string;
  sessionId: string;
}

/**
 * Initialize or retrieve user and session IDs from localStorage
 * User ID comes from backend login response, session ID is generated locally
 */
export const initializeSession = (): SessionIds => {
  // Get user ID from backend (stored during login)
  let userId = localStorage.getItem('moneymentor_user_id');
  if (!userId) {
    // If no user ID, user is not authenticated
    throw new Error('User not authenticated');
  }

  // Get session ID from localStorage
  let sessionId = localStorage.getItem(STORAGE_KEYS.SESSION_ID);
  if (!sessionId) {
    // If no session ID, generate a new UUID for new chat
    sessionId = uuidv4();
    localStorage.setItem(STORAGE_KEYS.SESSION_ID, sessionId);
  }

  return { userId, sessionId };
};

/**
 * Set session ID to a new UUID for new chat creation
 * This will trigger backend to create a new session when first message is sent
 */
export const setNewChatSession = (): void => {
  localStorage.setItem(STORAGE_KEYS.SESSION_ID, uuidv4());
};

/**
 * Set active session ID
 */
export const setActiveSession = (sessionId: string): void => {
  localStorage.setItem(STORAGE_KEYS.SESSION_ID, sessionId);
};

/**
 * Clear session data from localStorage
 */
export const clearSession = (): void => {
  localStorage.removeItem(STORAGE_KEYS.SESSION_ID);
  // Note: We don't remove USER_ID here as it should persist across sessions
  // It will be removed during logout
};

/**
 * Get current session IDs without generating new ones
 */
export const getCurrentSession = (): SessionIds | null => {
  const userId = localStorage.getItem('moneymentor_user_id');
  const sessionId = localStorage.getItem(STORAGE_KEYS.SESSION_ID);
  
  if (!userId || !sessionId) {
    return null;
  }
  
  return { userId, sessionId };
};

/**
 * Check if current session is a new chat (no previous messages)
 * Note: We can't reliably detect this anymore since we use UUIDs
 * This function is kept for backward compatibility but always returns false
 */
export const isNewChatSession = (): boolean => {
  // Since we now use UUIDs instead of "dummy", we can't reliably detect new sessions
  // The backend will handle session creation when needed
  return false;
}; 