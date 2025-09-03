import React from 'react';
import { X, Trophy, Star, CheckCircle } from 'lucide-react';
import '../../styles/ChatWidget.css';

interface CongratulationsModalProps {
  isVisible: boolean;
  onClose: () => void;
  score?: number;
  courseTitle?: string;
}

export const CongratulationsModal: React.FC<CongratulationsModalProps> = ({
  isVisible,
  onClose,
  score,
  courseTitle
}) => {
  if (!isVisible) {
    return null;
  }

  return (
    <div className="congratulations-modal-overlay">
      <div className="congratulations-modal">
        <div className="congratulations-modal-header">
          <button 
            onClick={onClose}
            className="congratulations-modal-close"
            aria-label="Close"
          >
            <X size={24} />
          </button>
        </div>
        
        <div className="congratulations-modal-content">
          <div className="congratulations-icon">
            <Trophy size={64} className="trophy-icon" />
            <div className="stars-container">
              <Star size={20} className="star star-1" />
              <Star size={16} className="star star-2" />
              <Star size={18} className="star star-3" />
            </div>
          </div>
          
          <h2 className="congratulations-title">🎉 Congratulations! 🎉</h2>
          
          <p className="congratulations-message">
            You've successfully completed
            {courseTitle && <span className="course-title-highlight"> "{courseTitle}"</span>}!
          </p>
          
          {score !== undefined && (
            <div className="score-display">
              <CheckCircle size={20} />
              <span>Final Score: <strong>{score}%</strong></span>
            </div>
          )}
          
          <p className="congratulations-subtitle">
            You've taken an important step toward improving your financial knowledge. 
            Keep up the great work!
          </p>
          
          <div className="achievement-badges">
            <div className="achievement-badge">
              <CheckCircle size={16} />
              <span>Course Completed</span>
            </div>
            <div className="achievement-badge">
              <Star size={16} />
              <span>Knowledge Gained</span>
            </div>
            <div className="achievement-badge">
              <Trophy size={16} />
              <span>Milestone Reached</span>
            </div>
          </div>
        </div>
        
        <div className="congratulations-modal-footer">
          <button 
            onClick={onClose}
            className="continue-learning-btn"
          >
            Continue Learning
          </button>
        </div>
      </div>
    </div>
  );
}; 