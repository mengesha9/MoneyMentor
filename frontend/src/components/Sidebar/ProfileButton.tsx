import React from 'react';
import { UserProfile } from '../../types';
import { getUserInitials } from '../../utils/profile';

interface ProfileButtonProps {
  userProfile: UserProfile;
  isCollapsed: boolean;
  onClick: () => void;
}

export const ProfileButton: React.FC<ProfileButtonProps> = ({
  userProfile,
  isCollapsed,
  onClick
}) => {
  const initials = getUserInitials(userProfile.name);

  return (
    <div className="sidebar-profile">
      <button className="profile-button" onClick={onClick}>
        <div className="profile-avatar">
          {userProfile.avatar && userProfile.avatar !== '👤' ? (
            <span>{userProfile.avatar}</span>
          ) : (
            <span>{initials}</span>
          )}
        </div>

        {!isCollapsed && (
          <div className="profile-info">
            <div className="profile-name">{userProfile.name}</div>
          </div>
        )}
      </button>
    </div>
  );
}; 