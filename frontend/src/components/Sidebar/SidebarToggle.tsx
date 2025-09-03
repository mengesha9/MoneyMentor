import React from 'react';

interface SidebarToggleProps {
  isOpen: boolean;
  onClick: () => void;
  className?: string;
}

export const SidebarToggle: React.FC<SidebarToggleProps> = ({
  isOpen,
  onClick,
  className = ''
}) => {
  return (
    <button
      className={`sidebar-toggle ${className}`}
      onClick={onClick}
      title={isOpen ? 'Close sidebar' : 'Open sidebar'}
      style={{
        width: '32px',
        height: '32px',
        border: 'none',
        borderRadius: '6px',
        background: 'rgba(255, 255, 255, 0.15)',
        color: 'white',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '14px',
        transition: 'all 0.2s ease',
        backdropFilter: 'blur(10px)',
        WebkitBackdropFilter: 'blur(10px)',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.25)';
        e.currentTarget.style.transform = 'scale(1.05)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.15)';
        e.currentTarget.style.transform = 'scale(1)';
      }}
    >
      {isOpen ? '✕' : '☰'}
    </button>
  );
}; 