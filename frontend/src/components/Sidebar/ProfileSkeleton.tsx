import React from 'react';
import './ProfileSkeleton.css';

interface ProfileSkeletonProps {
  theme?: 'light' | 'dark';
}

export const ProfileSkeleton: React.FC<ProfileSkeletonProps> = ({ theme = 'light' }) => {
  const shimmerClass = theme === 'dark' ? 'shimmer-dark' : 'shimmer-light';
  
  return (
    <div className={`profile-skeleton ${theme}`} data-testid="profile-skeleton">
      {/* Profile Header Skeleton */}
      <div className="profile-header-skeleton">
        <div className={`avatar-skeleton ${shimmerClass}`}></div>
        <div className="profile-details-skeleton">
          <div className={`name-skeleton ${shimmerClass}`}></div>
          <div className={`email-skeleton ${shimmerClass}`}></div>
          <div className={`date-skeleton ${shimmerClass}`}></div>
        </div>
      </div>

      {/* Stats Grid Skeleton */}
      <div className="stats-grid-skeleton">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="stat-item-skeleton">
            <div className={`stat-value-skeleton ${shimmerClass}`}></div>
            <div className={`stat-label-skeleton ${shimmerClass}`}></div>
          </div>
        ))}
      </div>
    </div>
  );
}; 