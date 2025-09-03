import Cookies from 'js-cookie';

/**
 * Test utility to simulate session expiration
 * This can be used to test the session expired modal
 */
export const testSessionExpiration = () => {
  // Set a token that expires in 1 second
  const testToken = 'test_token_123';
  const expires = new Date(Date.now() + 1000); // 1 second from now
  
  Cookies.set('auth_token', testToken, { expires });
  localStorage.setItem('auth_token_expires', expires.toISOString());
  
 
};

/**
 * Test utility to simulate session expiration in 5 minutes
 */
export const testSessionExpirationWarning = () => {
  // Set a token that expires in 5 minutes
  const testToken = 'test_token_123';
  const expires = new Date(Date.now() + 5 * 60 * 1000); // 5 minutes from now
  
  Cookies.set('auth_token', testToken, { expires });
  localStorage.setItem('auth_token_expires', expires.toISOString());
  
 
};

/**
 * Clear test session
 */
export const clearTestSession = () => {
  Cookies.remove('auth_token');
  localStorage.removeItem('auth_token_expires');
 
}; 