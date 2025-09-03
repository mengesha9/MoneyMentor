import { useState, useEffect } from 'react';
import { initializeSession, SessionIds } from '../utils/chatWidget';

export const useSessionState = () => {
  const [sessionIds, setSessionIds] = useState<SessionIds>({ userId: '', sessionId: '' });

  // Initialize session on component mount
  useEffect(() => {
    try {
    const ids = initializeSession();
    setSessionIds(ids);
    } catch (error) {
      // If user is not authenticated, sessionIds will remain empty
      // This is expected when the user hasn't logged in yet
      console.log('User not authenticated, session not initialized');
    }
  }, []);

  return {
    sessionIds,
    setSessionIds
  };
}; 