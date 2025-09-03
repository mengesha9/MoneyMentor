# Session Expiration Modal Feature

## Overview

The frontend now includes a session expiration modal that appears when a user's session is about to expire or has already expired. This feature helps improve user experience by giving users the option to extend their session rather than being automatically logged out.

## How It Works

### 1. Session Tracking
- The system tracks session expiration using both cookies and localStorage
- When a user logs in, the expiration time is stored in localStorage for accurate tracking
- The system checks session status every second

### 2. Expiration Detection
The modal appears in two scenarios:
- **Session has expired**: When the auth_token cookie is no longer present
- **Session is about to expire**: When the session will expire within 5 minutes

### 3. Modal Options
When the modal appears, users can:
- **Stay Logged In**: Extend their session with the option to:
  - Keep logged in for 30 days (default)
  - Keep logged in for 2 hours only
- **Logout**: Immediately log out and clear the session

## Implementation Details

### Files Created/Modified

1. **`SessionExpiredModal.tsx`** - New component for the session expired modal
2. **`sessionUtils.ts`** - Utility functions for session management
3. **`AuthModal.tsx`** - Updated to store expiration time in localStorage
4. **`ChatWidget.tsx`** - Updated to include session expiration detection
5. **`sessionTest.ts`** - Test utilities for demonstrating the feature

### Key Functions

#### Session Utilities (`sessionUtils.ts`)
- `getSessionInfo()`: Get current session information including expiration
- `isSessionExpiredOrExpiringSoon()`: Check if session is expired or expiring soon
- `extendSession()`: Extend session with new expiration
- `clearSession()`: Clear session and localStorage

#### Session Expired Modal (`SessionExpiredModal.tsx`)
- Displays when session is expired or expiring soon
- Allows users to choose session extension duration
- Provides logout option

## Cookie Age Settings

The system uses two different cookie expiration settings:

1. **"Keep me logged in" (checked)**: 30 days
2. **"Keep me logged in" (unchecked)**: 2 hours

## Testing the Feature

You can test the session expiration modal using the test utilities:

```javascript
import { testSessionExpiration, testSessionExpirationWarning, clearTestSession } from './utils/sessionTest';

// Test immediate expiration (1 second)
testSessionExpiration();

// Test warning expiration (5 minutes)
testSessionExpirationWarning();

// Clear test session
clearTestSession();
```

## User Experience

1. **Proactive Warning**: Users see the modal 5 minutes before expiration
2. **Flexible Options**: Users can choose session duration
3. **Graceful Handling**: No sudden logouts without warning
4. **Consistent UI**: Modal matches the existing design system

## Security Considerations

- Session expiration is enforced on both client and server side
- Tokens are properly cleared from both cookies and localStorage
- Users are always given the choice to logout immediately
- Session extension requires user consent

## Browser Compatibility

- Uses `js-cookie` library for cross-browser cookie handling
- Uses `localStorage` for expiration tracking (supported in all modern browsers)
- Graceful fallback if localStorage is not available

## Session Configuration

- **Access Token Expiration**: 60 minutes (matches backend configuration)
- **Refresh Token Expiration**: 7 days
- **Warning Time**: 5 minutes before expiration
- **Auto-logout Timeout**: 60 seconds if user doesn't respond to modal 