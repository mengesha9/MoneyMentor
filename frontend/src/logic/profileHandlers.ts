import { ProfileHandlersProps, UserProfile } from '../types';
import { isValidEmail } from '../utils/profile';

// Handle profile modal open
export const handleOpenProfileModal = (
  tab: 'profile' | 'settings',
  props: ProfileHandlersProps
) => {
  const { setProfileModalState } = props;
  
  setProfileModalState({
    isOpen: true,
    activeTab: tab,
  });
};

// Handle profile modal close
export const handleCloseProfileModal = (props: ProfileHandlersProps) => {
  const { setProfileModalState } = props;
  
  setProfileModalState({
    isOpen: false,
    activeTab: 'profile',
  });
};

// Handle tab switch in profile modal
export const handleTabSwitch = (
  tab: 'profile' | 'settings',
  props: ProfileHandlersProps
) => {
  const { profileModalState, setProfileModalState } = props;
  
  setProfileModalState({
    ...profileModalState,
    activeTab: tab,
  });
};

// Handle profile name update
export const handleNameUpdate = async (
  newName: string,
  props: ProfileHandlersProps
) => {
  const { onProfileUpdate } = props;
  
  try {
    if (newName.trim().length < 2) {
      throw new Error('Name must be at least 2 characters long');
    }
    
    await onProfileUpdate({ name: newName.trim() });
    return { success: true };
  } catch (error) {
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'Failed to update name' 
    };
  }
};

// Handle email update
export const handleEmailUpdate = async (
  newEmail: string,
  props: ProfileHandlersProps
) => {
  const { onProfileUpdate } = props;
  
  try {
    if (!isValidEmail(newEmail)) {
      throw new Error('Please enter a valid email address');
    }
    
    await onProfileUpdate({ email: newEmail.trim() });
    return { success: true };
  } catch (error) {
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'Failed to update email' 
    };
  }
};

// Handle theme toggle
export const handleThemeToggle = async (props: ProfileHandlersProps) => {
  const { userProfile, onProfileUpdate } = props;
  
  try {
    const newTheme = userProfile.preferences.theme === 'light' ? 'dark' : 'light';
    
    await onProfileUpdate({
      preferences: {
        ...userProfile.preferences,
        theme: newTheme,
      },
    });
    
    return { success: true, theme: newTheme };
  } catch (error) {
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'Failed to toggle theme' 
    };
  }
};









// Handle account deletion (mock implementation)
export const handleAccountDeletion = async (props: ProfileHandlersProps) => {
  const { onProfileUpdate } = props;
  
  try {
    // Mock account deletion - in real app this would call API
   
    
    // For now, just log out the user
    await onProfileUpdate({
      preferences: {
        theme: 'light',
        notifications: false,
        autoSave: false,
      },
    });
    
    return { success: true };
  } catch (error) {
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'Failed to delete account' 
    };
  }
};

// Handle modal backdrop click
export const handleModalBackdropClick = (
  event: React.MouseEvent<HTMLDivElement>,
  props: ProfileHandlersProps
) => {
  // Close modal if clicking on backdrop
  if (event.target === event.currentTarget) {
    handleCloseProfileModal(props);
  }
};

// Handle escape key press in modal
export const handleModalEscapeKey = (
  event: KeyboardEvent,
  props: ProfileHandlersProps
) => {
  if (event.key === 'Escape') {
    handleCloseProfileModal(props);
  }
}; 