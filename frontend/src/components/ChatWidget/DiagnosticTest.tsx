import React from 'react';
import '../../styles/ChatWidget.css';
import { QuizQuestion, QuizFeedback } from '../../types';

interface DiagnosticTestProps {
  isDiagnosticMode: boolean;
  currentQuiz: QuizQuestion | null;
  showDiagnosticFeedback: boolean;
  diagnosticFeedback: QuizFeedback | null;
  diagnosticQuestionIndex: number;
  diagnosticTotalQuestions: number;
  onDiagnosticQuizAnswer: (selectedOption: number, correct: boolean) => void;
  onCompleteDiagnosticTest?: (state: any) => void;
  onNextDiagnosticQuestion?: () => void;
}

export const DiagnosticTest: React.FC<DiagnosticTestProps> = ({
  isDiagnosticMode,
  currentQuiz,
  showDiagnosticFeedback,
  diagnosticFeedback,
  diagnosticQuestionIndex,
  diagnosticTotalQuestions,
  onDiagnosticQuizAnswer,
  onCompleteDiagnosticTest,
  onNextDiagnosticQuestion
}) => {
  console.log('🔍 DiagnosticTest render state:', {
    isDiagnosticMode,
    currentQuiz: !!currentQuiz,
    currentQuizData: currentQuiz,
    showDiagnosticFeedback,
    diagnosticQuestionIndex,
    diagnosticTotalQuestions
  });
  
  if (!isDiagnosticMode || (!currentQuiz && !showDiagnosticFeedback)) {
    console.log('🔍 DiagnosticTest returning null - conditions not met');
    return null;
  }

  return (
    <div className="diagnostic-container">
      {/* Progress indicator is now handled by parent component */}
      <div className="diagnostic-header" style={{ display: 'none' }}>
        <div className="diagnostic-progress">
          <div className="progress-circle">
            <span className="progress-current">{diagnosticQuestionIndex + 1}</span>
            <span className="progress-total">/ {diagnosticQuestionIndex + 1}</span>
          </div>
        </div>
      </div>

      {/* Show question or feedback */}
      {currentQuiz && !showDiagnosticFeedback && (
        <>
          <div className="diagnostic-question">
            <h3>{currentQuiz.question}</h3>
          </div>

          <div className="diagnostic-options">
            {currentQuiz.options.map((option, index) => (
              <button
                key={index}
                onClick={() => onDiagnosticQuizAnswer(index, index === currentQuiz?.correctAnswer)}
                className="diagnostic-option"
              >
                <div className="option-indicator">
                  {String.fromCharCode(65 + index)}
                </div>
                <span className="option-text">{option}</span>
              </button>
            ))}
          </div>

          {/* <div className="diagnostic-footer">
            <span className="diagnostic-hint">💭 Choose the best answer</span>
          </div> */}
        </>
      )}

      {/* Show feedback in place of question */}
      {showDiagnosticFeedback && diagnosticFeedback && (
        <div className={`diagnostic-feedback-container ${diagnosticFeedback.correct ? 'correct' : 'incorrect'}`}>
          <div className="feedback-header">
            <div className="feedback-icon-container">
              <span className="feedback-icon">
                {diagnosticFeedback.correct ? '🎉' : '🤔'}
              </span>
            </div>
            <div className="feedback-content">
              <div className="feedback-title">
                {diagnosticFeedback.correct ? 'Excellent!' : 'Good Try!'}
              </div>
              <div className="feedback-subtitle">
                {diagnosticFeedback.correct ? 'You got it right!' : 'Here\'s what you should know:'}
              </div>
            </div>
          </div>
          
          <div className="feedback-explanation">
            <div className="explanation-icon">💡</div>
            <p>{diagnosticFeedback.explanation}</p>
          </div>
          
          <div className="feedback-footer">
            <div className="feedback-progress-dots">
              {Array.from({ length: diagnosticTotalQuestions }, (_, i) => (
                <span 
                  key={i} 
                  className={`dot ${i <= diagnosticQuestionIndex ? 'active' : ''}`}
                ></span>
              ))}
            </div>
            {onNextDiagnosticQuestion && (
              <button 
                className="next-question-button"
                onClick={onNextDiagnosticQuestion}
              >
                Next Question
              </button>
            )}
          </div>
        </div>
      )}
      
      {/* Show completion message when test is done */}
      {diagnosticTotalQuestions > 0 && diagnosticQuestionIndex >= diagnosticTotalQuestions - 1 && !currentQuiz && !showDiagnosticFeedback && (
        <div className="diagnostic-completion">
          <div className="completion-content">
            <h3>🎯 Diagnostic Test Complete!</h3>
            <p>Thank you for completing the assessment. Your results are being processed...</p>
            {onCompleteDiagnosticTest && (
              <button 
                className="complete-test-button"
                onClick={() => onCompleteDiagnosticTest({
                  test: { questions: [], totalQuestions: diagnosticTotalQuestions, passingScore: 0 },
                  currentQuestionIndex: diagnosticQuestionIndex,
                  answers: [],
                  isActive: false,
                  quizId: ''
                })}
              >
                View Results
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}; 