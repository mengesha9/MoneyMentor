import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, CheckCircle } from 'lucide-react';
import '../../styles/ChatWidget.css';
import { CourseQuizState, CourseQuizAnswers } from '../../utils/chatWidget';

interface CourseQuizProps {
  courseQuiz: CourseQuizState | null;
  courseQuizAnswers: CourseQuizAnswers;
  onCourseQuizAnswerSelection: (questionIndex: number, selectedOption: number) => void;
  onCourseQuizNavigation: (direction: 'next' | 'previous' | number) => void;
  onSubmitCourseQuiz: (selectedOption: number, correct: boolean) => void;
  areAllQuestionsAnswered: (answers: number[]) => boolean;
}

export const CourseQuiz: React.FC<CourseQuizProps> = ({
  courseQuiz,
  courseQuizAnswers,
  onCourseQuizAnswerSelection,
  onCourseQuizNavigation,
  onSubmitCourseQuiz,
  areAllQuestionsAnswered
}) => {
  const [showSummary, setShowSummary] = useState(false);
  const [quizResult, setQuizResult] = useState<{ correct: boolean; explanation: string } | null>(null);

  if (!courseQuiz || !Array.isArray(courseQuiz.questions) || courseQuiz.questions.length === 0) {
    return <div className="course-quiz-container"><div className="course-quiz-header"><h3>Course Quiz</h3></div><div>No quiz questions available.</div></div>;
  }

  const currentQuestion = courseQuiz.questions[0]; // For single question quizzes
  if (!currentQuestion || !Array.isArray(currentQuestion.options)) {
    return <div className="course-quiz-container"><div className="course-quiz-header"><h3>Course Quiz</h3></div><div>Invalid quiz question format.</div></div>;
  }

  const selectedAnswer = courseQuizAnswers.answers[0];
  const hasAnswered = selectedAnswer !== -1;

  const handleAnswerSelection = (optionIndex: number) => {
    onCourseQuizAnswerSelection(0, optionIndex);
  };

  const handleNext = () => {
    if (!showSummary && hasAnswered) {
      // First click: submit answer and show summary
      const correct = selectedAnswer === currentQuestion.correctAnswer;
      setQuizResult({ correct, explanation: currentQuestion.explanation || 'Good job!' });
      setShowSummary(true);
    } else if (showSummary) {
      // Second click: proceed to next page
      const correct = selectedAnswer === currentQuestion.correctAnswer;
      onSubmitCourseQuiz(selectedAnswer, correct);
    }
  };

  if (showSummary && quizResult) {
    return (
      <div className="course-quiz-container">
        <div className="course-quiz-header">
          <div className="quiz-title">
            <span className="quiz-icon">🎯</span>
            <h3>Quiz Summary</h3>
          </div>
          <div className="quiz-progress">
            Quiz Page {courseQuiz.pageIndex + 1} of {courseQuiz.totalPages}
          </div>
        </div>
        
        <div className="quiz-summary">
          <div className={`quiz-result ${quizResult.correct ? 'correct' : 'incorrect'}`}>
            <div className="result-icon">
              {quizResult.correct ? '🎉' : '🤔'}
            </div>
            <div className="result-text">
              <h4>{quizResult.correct ? 'Correct!' : 'Not quite right'}</h4>
              <p>{quizResult.explanation}</p>
            </div>
          </div>
          
          <div className="question-review">
            <h5>Question:</h5>
            <p>{currentQuestion.question}</p>
            
            <div className="answer-review">
              <div className="your-answer">
                <strong>Your answer:</strong> {String.fromCharCode(65 + selectedAnswer)} - {currentQuestion.options[selectedAnswer]}
              </div>
              {!quizResult.correct && (
                <div className="correct-answer">
                  <strong>Correct answer:</strong> {String.fromCharCode(65 + currentQuestion.correctAnswer)} - {currentQuestion.options[currentQuestion.correctAnswer]}
                </div>
              )}
            </div>
          </div>
        </div>
        
        <div className="course-quiz-navigation">
          <button
            onClick={() => onCourseQuizNavigation('previous')}
            className="quiz-nav-btn quiz-nav-prev"
            disabled={courseQuiz.pageIndex === 0}
          >
            <ChevronLeft size={14} />
            Back
          </button>
          
          <div className="quiz-nav-buttons">
            <button
              onClick={handleNext}
              className="quiz-nav-btn submit-quiz-btn"
            >
              <ChevronRight size={14} />
              Next
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="course-quiz-container">
      <div className="course-quiz-header">
        <div className="quiz-title">
          <span className="quiz-icon">🎯</span>
          <h3>Course Quiz</h3>
        </div>
        <div className="quiz-progress">
          Quiz Page {courseQuiz.pageIndex + 1} of {courseQuiz.totalPages}
        </div>
      </div>
      
      <div className="single-quiz-question">
        <div className="course-quiz-question">
          <div className="question-header">
            <span className="question-number">Question 1</span>
            <span className="question-difficulty">{currentQuestion.difficulty || 'medium'}</span>
          </div>
          <p className="question-text">{currentQuestion.question}</p>
          <div className="question-options">
            {currentQuestion.options.map((option, optionIndex) => (
              <button
                key={optionIndex}
                onClick={() => handleAnswerSelection(optionIndex)}
                className={`quiz-option ${selectedAnswer === optionIndex ? 'selected' : ''}`}
              >
                <div className="option-indicator">
                  {String.fromCharCode(65 + optionIndex)}
                </div>
                <span className="option-text">{option}</span>
                {selectedAnswer === optionIndex && (
                  <CheckCircle size={16} className="option-check" />
                )}
              </button>
            ))}
          </div>
        </div>
      </div>
      
      <div className="course-quiz-navigation">
        <button
          onClick={() => onCourseQuizNavigation('previous')}
          className="quiz-nav-btn quiz-nav-prev"
          disabled={courseQuiz.pageIndex === 0}
        >
          <ChevronLeft size={14} />
          Back
        </button>
        
        <div className="quiz-nav-buttons">
          <button
            onClick={handleNext}
            disabled={!hasAnswered}
            className="quiz-nav-btn submit-quiz-btn"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}; 