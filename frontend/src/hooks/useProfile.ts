import { useState, useCallback, useEffect } from 'react';
import { ProfileModalState, UserProfile } from '../types';
import { getDefaultUserProfile } from '../utils/profile';
import { getStoredUserName } from '../utils/sessionUtils';

export const useProfile = () => {
  const [profileModalState, setProfileModalState] = useState<ProfileModalState>({
    isOpen: false,
    activeTab: 'profile',
  });

  const [userProfile, setUserProfile] = useState<UserProfile>(getDefaultUserProfile());

  // Initialize profile with stored name from localStorage
  useEffect(() => {
    const storedName = getStoredUserName();
    if (storedName) {
      setUserProfile(prev => ({
        ...prev,
        name: storedName,
      }));
    }
  }, []);

  const openProfileModal = useCallback((tab: 'profile' | 'settings' = 'profile') => {
    setProfileModalState({
      isOpen: true,
      activeTab: tab,
    });
  }, []);

  const closeProfileModal = useCallback(() => {
    setProfileModalState(prev => ({
      ...prev,
      isOpen: false,
    }));
  }, []);

  const switchTab = useCallback((tab: 'profile' | 'settings') => {
    setProfileModalState(prev => ({
      ...prev,
      activeTab: tab,
    }));
  }, []);

  const updateProfile = useCallback((updates: Partial<UserProfile>) => {
    setUserProfile(prev => ({
      ...prev,
      ...updates,
    }));
  }, []);

  const toggleTheme = useCallback(() => {
    setUserProfile(prev => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        theme: prev.preferences.theme === 'light' ? 'dark' : 'light',
      },
    }));
  }, []);

  return {
    profileModalState,
    setProfileModalState,
    userProfile,
    setUserProfile,
    openProfileModal,
    closeProfileModal,
    switchTab,
    updateProfile,
    toggleTheme,
  };
}; 