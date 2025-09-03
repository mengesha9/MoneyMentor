import React from 'react';
import './ChatSessionsSkeleton.css';

interface ChatSessionsSkeletonProps {
  theme?: 'light' | 'dark';
  isCollapsed?: boolean;
}

export const ChatSessionsSkeleton: React.FC<ChatSessionsSkeletonProps> = ({ 
  theme = 'light',
  isCollapsed = false
}) => {
  const shimmerClass = theme === 'dark' ? 'shimmer-dark' : 'shimmer-light';
  
  if (isCollapsed) {
    return (
      <div className="chat-sessions-skeleton collapsed" data-testid="chat-sessions-skeleton">
        {[1, 2, 3].map((i) => (
          <div key={i} className="session-item-skeleton-collapsed">
            <div className={`session-icon-skeleton ${shimmerClass}`}></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="chat-sessions-skeleton" data-testid="chat-sessions-skeleton">
      {/* Today Group */}
      <div className="session-group-skeleton">
        <div className={`session-group-title-skeleton ${shimmerClass}`}></div>
        {[1, 2].map((i) => (
          <div key={i} className="session-item-skeleton">
            <div className={`session-icon-skeleton ${shimmerClass}`}></div>
            <div className="session-content-skeleton">
              <div className={`session-title-skeleton ${shimmerClass}`}></div>
              <div className={`session-preview-skeleton ${shimmerClass}`}></div>
              <div className="session-meta-skeleton">
                <div className={`session-timestamp-skeleton ${shimmerClass}`}></div>
                <div className={`session-message-count-skeleton ${shimmerClass}`}></div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Yesterday Group */}
      <div className="session-group-skeleton">
        <div className={`session-group-title-skeleton ${shimmerClass}`}></div>
        {[3, 4, 5].map((i) => (
          <div key={i} className="session-item-skeleton">
            <div className={`session-icon-skeleton ${shimmerClass}`}></div>
            <div className="session-content-skeleton">
              <div className={`session-title-skeleton ${shimmerClass}`}></div>
              <div className={`session-preview-skeleton ${shimmerClass}`}></div>
              <div className="session-meta-skeleton">
                <div className={`session-timestamp-skeleton ${shimmerClass}`}></div>
                <div className={`session-message-count-skeleton ${shimmerClass}`}></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}; 