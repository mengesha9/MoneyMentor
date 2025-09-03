import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Typography,
  Box,
  FormControlLabel,
  Checkbox,
  Alert,
  Link,
  CircularProgress
} from '@mui/material';
import { registerUser, loginUser, logoutUser } from '../utils/chatWidget/api';
import { storeAuthData } from '../utils/sessionUtils';
import Cookies from 'js-cookie';

// Module-level variable to prevent multiple logout attempts
let logoutInProgress = false;

interface AuthModalProps {
  isOpen: boolean;
  onAuthSuccess: (userData?: any) => void;
  mode?: 'login' | 'register';
  onClose?: () => void;
}

const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onAuthSuccess, mode: initialMode = 'login', onClose }) => {
  const [mode, setMode] = useState<'login' | 'register'>(initialMode);

  // Update mode when prop changes
  useEffect(() => {
    setMode(initialMode);
  }, [initialMode]);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [keepLoggedIn, setKeepLoggedIn] = useState(true);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      let result;
      if (mode === 'register') {
        result = await registerUser(email, password, firstName, lastName);
      } else {
        result = await loginUser(email, password);
      }
      if (result && result.access_token && result.refresh_token && result.user?.id) {
        storeAuthData(result);
        onAuthSuccess(result);
        
        // Fetch user profile separately for better performance
        // This happens in the background and doesn't block the login
        setTimeout(async () => {
          try {
            const { getUserProfile } = await import('../utils/chatWidget/api');
            await getUserProfile();
          } catch (error) {
            console.warn('Could not fetch user profile after login:', error);
            // This is not critical - user is already logged in
          }
        }, 100);
      } else {
        setError('Invalid response from server. Please try again.');
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleModeToggle = () => {
    setMode(mode === 'login' ? 'register' : 'login');
    setError('');
  };

  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
          p: 1
        }
      }}
    >
      <DialogTitle sx={{ textAlign: 'center', pb: 1 }}>
        <Typography variant="h5" sx={{ fontWeight: 600, mb: 0.5 }}>
          {mode === 'login' ? 'Welcome Back' : 'Create Account'}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {mode === 'login' ? 'Sign in to continue' : 'Join MoneyMentor to start your financial journey'}
        </Typography>
      </DialogTitle>

      <DialogContent>
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
        {mode === 'register' && (
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <TextField
                fullWidth
                label="First Name"
              value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                required={mode === 'register'}
                size="small"
            />
              <TextField
                fullWidth
                label="Last Name"
              value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                required={mode === 'register'}
                size="small"
            />
            </Box>
        )}

          <TextField
            fullWidth
            label="Email"
          type="email"
          value={email}
            onChange={(e) => setEmail(e.target.value)}
          required
            size="small"
            sx={{ mb: 2 }}
        />

          <TextField
            fullWidth
            label="Password"
          type="password"
          value={password}
            onChange={(e) => setPassword(e.target.value)}
          required
            size="small"
            sx={{ mb: 2 }}
          />

          {/* Removed keepLoggedIn checkbox */}

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Button
            type="submit"
            fullWidth
            variant="contained"
            disabled={loading}
            sx={{ 
              mb: 2,
              py: 1.5,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              fontWeight: 600,
              fontSize: '1rem',
              '&:hover': {
                background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
                transform: 'translateY(-1px)',
                boxShadow: '0 4px 12px rgba(102, 126, 234, 0.3)'
              },
              '&:disabled': {
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                opacity: 0.7,
                transform: 'none'
              },
              transition: 'all 0.3s ease'
            }}
          >
            {loading ? (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CircularProgress 
                  size={20} 
                  sx={{ 
                    color: 'white',
                    '& .MuiCircularProgress-circle': {
                      strokeLinecap: 'round'
                    }
                  }} 
                />
                <Typography sx={{ fontWeight: 600 }}>
                  {mode === 'login' ? 'Signing In...' : 'Creating Account...'}
                </Typography>
              </Box>
            ) : (
              mode === 'login' ? 'Sign In' : 'Create Account'
            )}
          </Button>
        </Box>
      </DialogContent>

      <DialogActions sx={{ justifyContent: 'center', pb: 2 }}>
        <Typography variant="body2" color="text.secondary">
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <Link
            component="button"
            variant="body2"
            onClick={handleModeToggle}
            sx={{ cursor: 'pointer' }}
          >
            {mode === 'login' ? 'Sign Up' : 'Sign In'}
          </Link>
        </Typography>
      </DialogActions>
    </Dialog>
  );
};

export default AuthModal;

export const logout = async () => {
  // Prevent multiple logout attempts
  if (logoutInProgress) {
    return;
  }
  
  logoutInProgress = true;

  // Clear all auth data and reload immediately
  Cookies.remove('auth_token');

  localStorage.removeItem('auth_token_expires');
  localStorage.removeItem('moneymentor_user_id');
  localStorage.removeItem('moneymentor_user_name');
  localStorage.removeItem('moneymentor_session_id');

  // Fire-and-forget logout API call in the background
  try {
    const refreshToken = Cookies.get('refresh_token');
    if (refreshToken) {
      logoutUser(refreshToken); // Don't await
      Cookies.remove('refresh_token');
    }
  } catch (error) {
    // Ignore errors
  } finally {
    logoutInProgress = false;
    window.location.reload();
  }
};