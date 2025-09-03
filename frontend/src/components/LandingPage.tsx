import React, { useState } from 'react';
import { Box } from '@mui/material';
import { Navigation } from './Navigation';
import { HomePage } from './HomePage';
import AuthModal from './AuthModal';

interface LandingPageProps {
  onAuthSuccess: (authData: any) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onAuthSuccess }) => {
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

  const handleGetStarted = () => {
    setAuthMode('register');
    setShowAuthModal(true);
  };

  const handleLogin = () => {
    setAuthMode('login');
    setShowAuthModal(true);
  };

  const handleAuthSuccess = (authData: any) => {
    setShowAuthModal(false);
    onAuthSuccess(authData);
  };

  const handleCloseAuthModal = () => {
    setShowAuthModal(false);
  };

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ 
        behavior: 'smooth',
        block: 'start'
      });
    }
  };

  return (
    <Box sx={{ minHeight: '100vh' }}>
      <Navigation onGetStarted={handleGetStarted} onLogin={handleLogin} scrollToSection={scrollToSection} />
      <HomePage onGetStarted={handleGetStarted} />
      
      <AuthModal
        isOpen={showAuthModal}
        onAuthSuccess={handleAuthSuccess}
        mode={authMode}
        onClose={handleCloseAuthModal}
      />
    </Box>
  );
}; 