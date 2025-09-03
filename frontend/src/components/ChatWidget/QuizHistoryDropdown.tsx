import React, { useEffect, useRef, useState } from 'react';
import ReactDOM from 'react-dom';
import '../../styles/ChatWidget.css';
import Skeleton from 'react-loading-skeleton';

interface QuizHistoryDropdownProps {
  open: boolean;
  onClose: () => void;
  anchorRef: React.RefObject<HTMLElement>;
  quizHistory: Array<{
    question: string;
    options: string[];
    correctAnswer: number;
    userAnswer: number;
    explanation: string;
    topicTag?: string;
  }>;
  loading?: boolean;
  error?: string | null;
}

export const QuizHistoryDropdown: React.FC<QuizHistoryDropdownProps> = ({
  open,
  onClose,
  anchorRef,
  quizHistory,
  loading = false,
  error = null
}) => {
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState({ top: 0, left: 0 });

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handleClick = (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node) &&
        anchorRef.current &&
        !anchorRef.current.contains(e.target as Node)
      ) {
        onClose();
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [open, onClose, anchorRef]);

  // Position dropdown centered below anchor
  useEffect(() => {
    if (open && anchorRef.current) {
      const anchorRect = anchorRef.current.getBoundingClientRect();
      const dropdownWidth = 380;
      const top = anchorRect.bottom + 12;
      let left = anchorRect.left + anchorRect.width / 2 - dropdownWidth / 2;
      
      // Ensure it doesn't go off-screen
      if (left < 10) left = 10;
      if (left + dropdownWidth > window.innerWidth - 10) {
        left = window.innerWidth - dropdownWidth - 10;
      }
      
      setPosition({ top, left });
    }
  }, [open, anchorRef]);

  if (!open) return null;

  return ReactDOM.createPortal(
    <div 
      ref={dropdownRef} 
      className="quiz-history-dropdown"
      style={{
        position: 'fixed',
        top: position.top,
        left: position.left,
        width: '380px',
        maxHeight: '400px',
        zIndex: 99999,
      }}
    >
      {/* Arrow */}
      <div className="quiz-history-arrow">
        <svg width="38" height="18" viewBox="0 0 38 18" fill="none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="arrowGradient" x1="19" y1="0" x2="19" y2="18" gradientUnits="userSpaceOnUse">
              <stop stopColor="#f8fafc" stopOpacity="1"/>
              <stop offset="1" stopColor="#f8fafc" stopOpacity="0.0"/>
            </linearGradient>
          </defs>
          <path d="M0 0L19 18L38 0Z" fill="url(#arrowGradient)"/>
        </svg>
      </div>
      
      <div className="quiz-history-header">
        Quiz History
      </div>
      
      <div className="quiz-history-content">
        {loading ? (
          <div className="quiz-history-loading">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} height={60} style={{ marginBottom: 16, borderRadius: 12 }} />
            ))}
          </div>
        ) : error ? (
          <div className="quiz-history-error">{error}</div>
        ) : quizHistory.length === 0 ? (
          <div className="quiz-history-empty">
            No quizzes taken yet.
          </div>
        ) : (
          quizHistory.map((quiz, idx) => (
          <div key={idx} className="quiz-history-item">
            <div className="quiz-history-question">
              <span className="quiz-question-number">Q{idx + 1}:</span> {quiz.question}
            </div>
            <div className="quiz-history-options">
              {quiz.options.map((opt: string, i: number) => (
                <div
                  key={i}
                  className={`quiz-history-option ${
                    i === quiz.correctAnswer ? 'correct' : 
                    i === quiz.userAnswer ? 'user-answer' : ''
                  }`}
                >
                  <span className="option-letter">
                    {String.fromCharCode(65 + i)})
                  </span> 
                  <span className="option-text">{opt}</span>
                  {i === quiz.correctAnswer && (
                    <span className="correct-indicator">✔</span>
                  )}
                  {i === quiz.userAnswer && (
                    <span className="user-indicator">(You)</span>
                  )}
                </div>
              ))}
            </div>
            <div className="quiz-history-explanation">
              <span className="explanation-label">💡 Explanation:</span> {quiz.explanation}
            </div>
          </div>
          ))
        )}
      </div>
    </div>,
    document.body
  );
}; 