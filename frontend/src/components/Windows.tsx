import React, { useState, useRef, useEffect } from 'react';
import Skeleton from 'react-loading-skeleton';

interface WindowsProps {
  currentWindow: 'intro' | 'chat' | 'learn';
  onNavigateToChat: () => void;
  onNavigateToLearn: () => void;
  onNavigateToIntro: () => void;
  chatChildren: React.ReactNode;
  learnChildren: React.ReactNode;
  isExpanded?: boolean;
  hasUploads?: boolean;
  // Quiz tracker props
  showQuizDropdown?: boolean;
  onToggleQuizDropdown?: () => void;
  onCloseQuizDropdown?: () => void;
  quizTrackerRef?: React.RefObject<HTMLButtonElement>;
  chatQuizCorrectAnswered?: number;
  chatQuizTotalAnswered?: number;
  chatQuizHistory?: any[];
  QuizHistoryDropdown?: React.ComponentType<any>;
  // Missing props
  onQuizTrackerClick?: () => void;
  quizProgressLoading?: boolean;
  quizHistoryLoading?: boolean;
  quizHistoryError?: string | null;
}

export const Windows: React.FC<WindowsProps> = ({
  currentWindow,
  onNavigateToChat,
  onNavigateToLearn,
  onNavigateToIntro,
  chatChildren,
  learnChildren,
  isExpanded = false,
  hasUploads = false,
  // Quiz tracker props
  showQuizDropdown = false,
  onToggleQuizDropdown,
  onCloseQuizDropdown,
  quizTrackerRef,
  chatQuizCorrectAnswered = 0,
  chatQuizTotalAnswered = 0,
  chatQuizHistory = [],
  QuizHistoryDropdown,
  // Missing props
  onQuizTrackerClick,
  quizProgressLoading = false,
  quizHistoryLoading = false,
  quizHistoryError = null
}) => {
  return (
    <>
      {/* Quiz Tracker Button - Only visible in chat mode */}
      {currentWindow === 'chat' && onToggleQuizDropdown && quizTrackerRef && QuizHistoryDropdown && (
        <div 
          className="quiz-tracker-button"
          style={{
            position: 'absolute',
            top: '70px',
            right: '20px',
            zIndex: 1000
          }}
        >
          <button
            ref={quizTrackerRef}
            className="quiz-progress-simple-btn"
            onClick={onQuizTrackerClick}
            title="View quiz history"
            style={{ 
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 12px rgba(102, 126, 234, 0.3)',
              transition: 'all 0.2s ease',
              color: 'white',
              fontSize: '12px',
              fontWeight: '600',
              fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'scale(1.05)';
              e.currentTarget.style.boxShadow = '0 6px 16px rgba(102, 126, 234, 0.4)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'scale(1)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.3)';
            }}
          >
            {quizProgressLoading ? (
              <Skeleton width={32} height={16} baseColor="#a5b4fc" highlightColor="#c7d2fe" style={{ borderRadius: 8 }} />
            ) : (
            <span className="quiz-progress-simple-text" style={{ lineHeight: '1' }}>
              {chatQuizCorrectAnswered}/{chatQuizTotalAnswered}
            </span>
            )}
          </button>
          <QuizHistoryDropdown
            open={showQuizDropdown}
            onClose={onCloseQuizDropdown}
            anchorRef={quizTrackerRef}
            quizHistory={chatQuizHistory}
            loading={quizHistoryLoading}
            error={quizHistoryError}
          />
        </div>
      )}

      {/* Window Content */}
      {currentWindow === 'intro' && (
        <div className="intro-window">
          <div className="intro-content">
            <h2>Welcome to MoneyMentor! 💰</h2>
            <p>Choose how you'd like to get started:</p>
            
            <div className="intro-buttons">
              <button 
                className="intro-button chat-button"
                onClick={onNavigateToChat}
              >
                <div className="intro-icon">💬</div>
                <div className="intro-text">
                  <h3>Chat Mode</h3>
                  <p>Interactive conversations with AI assistance.</p>
                </div>
              </button>
              
              <button 
                className="intro-button learn-button"
                onClick={onNavigateToLearn}
              >
                <div className="intro-icon">📚</div>
                <div className="intro-text">
                  <h3>Learning Center</h3>
                  <p>Structured courses and educational content.</p>
                </div>
              </button>
            </div>
            
            <div style={{ marginTop: '20px', textAlign: 'center', fontSize: '12px', color: '#666', opacity: 0.7 }}>
              💡 <strong>Tip:</strong> You can switch between modes anytime using the navigation buttons. Maximize the window if you can't see the button for switching windows.
             </div>
          </div>
        </div>
      )}

      {currentWindow === 'chat' && (
        <div className="chat-window">
          {chatChildren}
        </div>
      )}

      {currentWindow === 'learn' && (
        <div className="chat-window">
          {learnChildren}
        </div>
      )}
    </>
  );
}; 