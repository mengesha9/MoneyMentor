import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  FormControlLabel,
  Checkbox,
  Alert
} from '@mui/material';
import Cookies from 'js-cookie';
import { refreshAccessToken } from '../utils/sessionUtils';

interface SessionExpiredModalProps {
  isOpen: boolean;
  onStayLoggedIn: () => void;
  onLogout: () => void;
}

const SessionExpiredModal: React.FC<SessionExpiredModalProps> = ({ 
  isOpen, 
  onStayLoggedIn, 
  onLogout 
}) => {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState('');

  const handleStayLoggedIn = async () => {
    setIsRefreshing(true);
    setError('');
    try {
      const success = await refreshAccessToken();
      if (success) {
      onStayLoggedIn();
      } else {
        setError('Failed to refresh session. Please log in again.');
      }
    } catch (error) {
      setError('Session refresh failed. Please log in again.');
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleLogout = () => {
    Cookies.remove('auth_token');
    Cookies.remove('refresh_token');
    localStorage.removeItem('auth_token_expires');
    localStorage.removeItem('moneymentor_user_id');
    localStorage.removeItem('moneymentor_session_id');
    onLogout();
  };

  return (
    <Dialog
      open={isOpen}
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
        <Box sx={{ textAlign: 'center', mb: 2 }}>
          <Typography variant="h3" sx={{ mb: 1 }}>⏰</Typography>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
            Session Expired
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Your session has expired. Would you like to refresh your session?
          </Typography>
        </Box>
      </DialogTitle>
        
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
          {/* Removed keepLoggedIn checkbox */}

          {error && (
            <Alert severity="error" sx={{ width: '100%' }}>
              {error}
            </Alert>
          )}
        </Box>
      </DialogContent>

      <DialogActions sx={{ justifyContent: 'center', gap: 2, pb: 2 }}>
        <Button
            onClick={handleStayLoggedIn}
          disabled={isRefreshing}
          variant="contained"
        >
          {isRefreshing ? 'Refreshing...' : 'Stay Logged In'}
        </Button>
        <Button
            onClick={handleLogout}
          variant="outlined"
          >
            Logout
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SessionExpiredModal; 