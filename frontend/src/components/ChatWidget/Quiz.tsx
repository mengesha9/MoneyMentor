import React from 'react';
import '../../styles/ChatWidget.css';
import { QuizQuestion, QuizFeedback } from '../../types';

interface QuizProps {
  currentQuiz: QuizQuestion | null;
  showQuizFeedback: boolean;
  lastQuizAnswer: QuizFeedback | null;
  isDiagnosticMode: boolean;
  onQuizAnswer: (selectedOption: number, correct: boolean) => void;
}

export const Quiz: React.FC<QuizProps> = ({
  currentQuiz,
  showQuizFeedback,
  lastQuizAnswer,
  isDiagnosticMode,
  onQuizAnswer
}) => {
  // Don't show micro quiz if in diagnostic mode
  if (!currentQuiz || isDiagnosticMode) {
    return (
      <>
        {/* Enhanced Quiz Feedback */}
        {showQuizFeedback && lastQuizAnswer && (
          <div className={`quiz-feedback-container ${lastQuizAnswer.correct ? 'correct' : 'incorrect'}`}>
            <div className="feedback-header">
              <div className="feedback-icon-container">
                <span className="feedback-icon">
                  {lastQuizAnswer.correct ? '🎉' : '🤔'}
                </span>
              </div>
              <div className="feedback-content">
                <div className="feedback-title">
                  {lastQuizAnswer.correct ? 'Excellent!' : 'Good Try!'}
                </div>
                <div className="feedback-subtitle">
                  {lastQuizAnswer.correct ? 'You got it right!' : 'Here\'s what you should know:'}
                </div>
              </div>
            </div>
            
            <div className="feedback-explanation">
              <div className="explanation-icon">💡</div>
              <p>{lastQuizAnswer.explanation}</p>
            </div>
            
            <div className="feedback-footer">
              <div className="feedback-progress-dots">
                <span className="dot active"></span>
                <span className="dot active"></span>
                <span className="dot"></span>
              </div>
              <span className="feedback-auto-close">Auto-closing in 3s...</span>
            </div>
          </div>
        )}
      </>
    );
  }

  return (
    <>
      {/* Micro Quiz Question */}
      <div className="micro-quiz-container">
        <div className="micro-quiz-header">
          <div className="micro-quiz-badge">
            <span className="quiz-icon">💡</span>
            <span>Quick Knowledge Check</span>
          </div>
          <div className="quiz-topic-tag">
            {currentQuiz.topicTag.replace('_', ' ').toUpperCase()}
          </div>
        </div>
        
        <div className="micro-quiz-question">
          <p>{currentQuiz.question}</p>
        </div>
        
        <div className="micro-quiz-options">
          {currentQuiz.options.map((option, index) => (
            <button
              key={index}
              onClick={() => onQuizAnswer(index, index === currentQuiz.correctAnswer)}
              className="micro-quiz-option"
            >
              <div className="option-letter">
                {String.fromCharCode(65 + index)}
              </div>
              <span className="option-content">{option}</span>
            </button>
          ))}
        </div>
        
        <div className="micro-quiz-footer">
          <span className="quiz-hint">💭 Take your time to think it through!</span>
        </div>
      </div>

      {/* Enhanced Quiz Feedback */}
      {showQuizFeedback && lastQuizAnswer && (
        <div className={`quiz-feedback-container ${lastQuizAnswer.correct ? 'correct' : 'incorrect'}`}>
          <div className="feedback-header">
            <div className="feedback-icon-container">
              <span className="feedback-icon">
                {lastQuizAnswer.correct ? '🎉' : '🤔'}
              </span>
            </div>
            <div className="feedback-content">
              <div className="feedback-title">
                {lastQuizAnswer.correct ? 'Excellent!' : 'Good Try!'}
              </div>
              <div className="feedback-subtitle">
                {lastQuizAnswer.correct ? 'You got it right!' : 'Here\'s what you should know:'}
              </div>
            </div>
          </div>
          
          <div className="feedback-explanation">
            <div className="explanation-icon">💡</div>
            <p>{lastQuizAnswer.explanation}</p>
          </div>
          
          <div className="feedback-footer">
            <div className="feedback-progress-dots">
              <span className="dot active"></span>
              <span className="dot active"></span>
              <span className="dot"></span>
            </div>
            <span className="feedback-auto-close">Auto-closing in 3s...</span>
          </div>
        </div>
      )}
    </>
  );
}; 