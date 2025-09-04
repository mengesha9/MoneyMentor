import React, { useState } from 'react';
import { Course } from '../../types';
import { DiagnosticTest } from './DiagnosticTest';
import { CourseList } from './CourseList';
import { CoursePage as CoursePageComponent } from './CoursePage';
import { CourseQuiz } from './CourseQuiz';
import { Quiz } from './Quiz';
import { ShimmerLoading } from './ShimmerLoading';
import { handleNextDiagnosticQuestion } from '../../logic/diagnosticHandlers';

import '../../styles/ChatWidget.css';

export type LearningPage = 'courses' | 'diagnostic' | 'course-content' | 'course-quiz' | 'course-generation';

export interface LearningCenterProps {
  // Page state
  currentPage: LearningPage;
  onPageChange: (page: LearningPage) => void;
  
  // Course selection
  selectedCourseKey?: string;
  selectedCourseLabel?: string;
  
  // Diagnostic test state
  isDiagnosticMode: boolean;
  currentDiagnosticQuiz: any;
  showDiagnosticFeedback: boolean;
  diagnosticFeedback: any;
  diagnosticQuestionIndex: number;
  diagnosticTotalQuestions: number;
  diagnosticState?: any; // Add diagnostic state for score calculation
  onDiagnosticQuizAnswer: (selectedOption: number, correct: boolean) => void;
  onCompleteDiagnosticTest: (state: any) => void;
  setDiagnosticState?: (state: any) => void;
  setShowDiagnosticFeedback?: (show: boolean) => void;
  setDiagnosticFeedback?: (feedback: any) => void;
  
  // Course state
  availableCourses: Course[];
  currentCoursePage: any;
  currentCourse: any;
  courseQuiz: any;
  courseQuizAnswers: any;
  
  // Loading states
  diagnosticGenerating: boolean;
  courseGenerating: boolean;
  courseCompleting: boolean;
  quizSubmitting: boolean;
  courseGenerationLoading?: boolean; // New state for when course is being generated after diagnostic
  
  // Event handlers
  onStartDiagnosticTest: (courseKey: string) => void;
  onStartCourse: (courseId: string) => void;
  onNavigateCoursePage: (pageIndex: number) => void;
  onCompleteCourse: () => void;
  onCourseQuizAnswerSelection: (questionIndex: number, selectedOption: number) => void;
  onCourseQuizNavigation: (direction: 'next' | 'previous' | number) => void;
  onSubmitCourseQuiz: (selectedOption: number, correct: boolean) => void;
  areAllQuestionsAnswered: (answers: any) => boolean;
  onBackToCourses: () => void;
  

  
  // Theme
  theme: 'light' | 'dark';
}

export const LearningCenter: React.FC<LearningCenterProps> = ({
  currentPage,
  onPageChange,
  selectedCourseKey,
  selectedCourseLabel,
  isDiagnosticMode,
  currentDiagnosticQuiz,
  showDiagnosticFeedback,
  diagnosticFeedback,
  diagnosticQuestionIndex,
  diagnosticTotalQuestions,
  diagnosticState,
  onDiagnosticQuizAnswer,
  onCompleteDiagnosticTest,
  setDiagnosticState,
  setShowDiagnosticFeedback,
  setDiagnosticFeedback,
  availableCourses,
  currentCoursePage,
  currentCourse,
  courseQuiz,
  courseQuizAnswers,
  diagnosticGenerating,
  courseGenerating,
  courseCompleting,
  quizSubmitting,
  courseGenerationLoading,
  onStartDiagnosticTest,
  onStartCourse,
  onNavigateCoursePage,
  onCompleteCourse,
  onCourseQuizAnswerSelection,
  onCourseQuizNavigation,
  onSubmitCourseQuiz,
  areAllQuestionsAnswered,
  onBackToCourses,
  theme
}) => {
  
  const handleBackToCourses = () => {
    // Use the parent handler to properly reset all state
    onBackToCourses();
  };

  const handleBackToMain = () => {
    onPageChange('courses');
  };

  const handleCourseSelection = (courseKey: string, courseLabel: string) => {
    // Start diagnostic test for the selected course
    onStartDiagnosticTest(courseKey);
    onPageChange('diagnostic');
  };

  const renderHeader = () => {
    return (
      <div className="learning-center-header">
        {/* <div className="header-content">
          <h2>📚 Learning Center</h2>
        </div> */}
      </div>
    );
  };

  const renderFloatingBackButton = () => {
    // Hide floating back button for diagnostic page since we have inline button
    if (currentPage === 'courses' || currentPage === 'diagnostic') return null;
    
    return (
      <div className="floating-back-button-container">
        <button 
          className="floating-back-button"
          onClick={handleBackToCourses}
          title="Back to Course Selection"
        >
          <div className="floating-back-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M19 12H5M12 19L5 12L12 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <span className="floating-back-text">Courses</span>
        </button>
      </div>
    );
  };

  const renderCoursesPage = () => {
    const LEARN_COURSES = [
      { 
        key: 'money-goals-mindset', 
        label: 'Money, Goals and Mindset',
        description: 'Learn to set smart financial goals and develop a positive money mindset for your future'
      },
      { 
        key: 'budgeting-saving', 
        label: 'Budgeting and Saving',
        description: 'Master budgeting basics and build healthy saving habits for financial success'
      },
      { 
        key: 'college-planning-saving', 
        label: 'College Planning and Saving',
        description: 'Plan for college costs, find scholarships, and learn about student loans'
      },
      { 
        key: 'earning-income-basics', 
        label: 'Earning and Income Basics',
        description: 'Understand paychecks, first jobs, and smart money habits when you start earning'
      },
    ];

    // Define colors and icons for each course topic (same as MessageButtons)
    const getTopicStyle = (label: string) => {
      switch (label) {
        case 'Money, Goals and Mindset':
          return { 
            gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            icon: '🎯'
          };
        case 'Budgeting and Saving':
          return { 
            gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            icon: '💰'
          };
        case 'College Planning and Saving':
          return { 
            gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
            icon: '🎓'
          };
        case 'Earning and Income Basics':
          return { 
            gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
            icon: '💼'
          };
        default:
          return { 
            gradient: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
            icon: '📚'
          };
      }
    };

    return (
      <div className="courses-page">
        <div className="courses-intro">
          <h3>Choose Your Learning Path</h3>
          <p>Take a quick assessment to get personalized courses tailored just for you:</p>
        </div>
        
        <div className="learning-topic-buttons">
          {LEARN_COURSES.map((course, index) => {
            const style = getTopicStyle(course.label);
            return (
              <button
                key={index}
                className="learning-topic-button"
                onClick={() => handleCourseSelection(course.key, course.label)}
                style={{ background: style.gradient }}
              >
                <div className="topic-content">
                  <span className="topic-icon">{style.icon}</span>
                  <div className="topic-text">
                    <span className="topic-label">{course.label}</span>
                    <span className="topic-description">{course.description}</span>
                  </div>
                </div>
                <span className="topic-arrow">→</span>
              </button>
            );
          })}
        </div>
      </div>
    );
  };

  const renderDiagnosticPage = () => {
    return (
      <div className="diagnostic-page">
        {/* Modern Header Section */}
        <div className="diagnostic-header-modern">
          {/* Back Button on the Left (Desktop) */}
          <div className="header-back-button">
            <button 
              className="back-button-modern"
              onClick={handleBackToCourses}
              title="Back to Course Selection"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M19 12H5M12 19L5 12L12 5" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>

          <div className="header-main">
            <div className="header-content">
              <h3 className="header-title">Diagnostic Assessment</h3>
              <p className="header-subtitle">Let's personalize your learning journey</p>
              {selectedCourseLabel && (
                <div className="course-badge">
                  <span className="badge-icon">📚</span>
                  <span className="badge-text">{selectedCourseLabel}</span>
                </div>
              )}
            </div>
          </div>

          {/* Progress Indicator on the Right (Desktop) */}
          <div className="header-progress-circle">
            <div className="progress-text-row">
              {diagnosticTotalQuestions > 0 && !diagnosticGenerating ? (
                <>
                  <span className="progress-number">{diagnosticQuestionIndex + 1}</span>
                  <span className="progress-divider">/</span>
                  <span className="progress-total">{diagnosticTotalQuestions}</span>
                </>
              ) : (
                <>
                  <span className="progress-number">-</span>
                  <span className="progress-divider">/</span>
                  <span className="progress-total">-</span>
                </>
              )}
            </div>
          </div>

          {/* Mobile Buttons Container - Side by Side Below Text */}
          <div className="header-buttons-container">
            {/* Back Button (Mobile) */}
            <div className="header-back-button-mobile">
              <button 
                className="back-button-modern"
                onClick={handleBackToCourses}
                title="Back to Course Selection"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M19 12H5M12 19L5 12L12 5" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>

            {/* Progress Indicator (Mobile) */}
            <div className="header-progress-circle-mobile">
              <div className="progress-text-row">
                {diagnosticTotalQuestions > 0 && !diagnosticGenerating ? (
                  <>
                    <span className="progress-number">{diagnosticQuestionIndex + 1}</span>
                    <span className="progress-divider">/</span>
                    <span className="progress-total">{diagnosticTotalQuestions}</span>
                  </>
                ) : (
                  <>
                    <span className="progress-number">-</span>
                    <span className="progress-divider">/</span>
                    <span className="progress-total">-</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>


        
        {/* Content Section */}
        <div className="diagnostic-content">
          {(() => {
            const completionCondition = diagnosticTotalQuestions > 0 && diagnosticQuestionIndex === -1 && !diagnosticGenerating;
            console.log('🔍 Diagnostic content rendering state:', {
              diagnosticGenerating,
              diagnosticTotalQuestions,
              diagnosticQuestionIndex,
              currentDiagnosticQuiz: !!currentDiagnosticQuiz,
              completionCondition,
              breakdown: {
                hasQuestions: diagnosticTotalQuestions > 0,
                isCompleted: diagnosticQuestionIndex === -1,
                notGenerating: !diagnosticGenerating
              }
            });
            return null;
          })()}
          
          {diagnosticGenerating ? (
            <div className="diagnostic-loading-section">
              <div className="loading-spinner-container">
                <h3 className="loading-title">🎯 Generating Assessment</h3>
                <p className="loading-subtitle">Creating questions to test your knowledge level...</p>
                
                {/* Progress indicator */}
                <div className="generation-progress">
                  <div className="progress-bar">
                    <div className="progress-fill"></div>
                  </div>
                  <p className="progress-text">This usually takes 10-20 seconds...</p>
                </div>
                
              </div>
            </div>
          ) : diagnosticTotalQuestions > 0 && diagnosticQuestionIndex === -1 && !diagnosticGenerating ? (
            <div className="diagnostic-completion-section">
              <div className="completion-header">
                <h3 className="completion-title">Diagnostic Assessment Complete!</h3>
                <p className="completion-subtitle">Great job! You've completed all {diagnosticTotalQuestions} questions.</p>
              </div>
              
              {/* Show assessment results */}
              <div className="assessment-results">
                <div className="results-summary">
                  <h4>📊 Your Assessment Summary</h4>
                  <div className="results-grid">
                    <div className="result-item">
                      <span className="result-label">Score:</span>
                      <span className="result-value">
                        {(() => {
                          // Calculate score based on answers
                          const correctAnswers = diagnosticState?.answers.filter((answer, index) => 
                            answer === diagnosticState?.test?.questions[index]?.correctAnswer
                          ).length;
                          const totalQuestions = diagnosticState?.test?.questions.length || 0;
                          const score = totalQuestions > 0 ? Math.round((correctAnswers / totalQuestions) * 100) : 0;
                          return `${score}%`;
                        })()}
                      </span>
                    </div>
                    <div className="result-item">
                      <span className="result-label">Course Focus:</span>
                      <span className="result-value">{selectedCourseLabel || 'Personalized Learning'}</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="completion-actions">
                <button 
                  className="complete-assessment-button"
                  onClick={() => {
                    console.log('🎯 Diagnostic completion button clicked:', {
                      diagnosticTotalQuestions,
                      diagnosticQuestionIndex,
                      currentDiagnosticQuiz: !!currentDiagnosticQuiz,
                      diagnosticState: diagnosticState
                    });
                    if (onCompleteDiagnosticTest && diagnosticState) {
                      onCompleteDiagnosticTest({
                        test: diagnosticState.test,
                        currentQuestionIndex: diagnosticState.currentQuestionIndex,
                        answers: diagnosticState.answers,
                        isActive: diagnosticState.isActive,
                        quizId: diagnosticState.quizId,
                        selectedCourseType: diagnosticState.selectedCourseType
                      });
                    }
                  }}
                >
                  <span className="button-icon">🚀</span>
                  <span className="button-text">Generate My Personalized Course</span>
                </button>
              </div>
            </div>
          ) : (
            <>
              {console.log('🔍 Rendering DiagnosticTest with:', {
                isDiagnosticMode,
                currentDiagnosticQuiz: !!currentDiagnosticQuiz,
                currentDiagnosticQuizData: currentDiagnosticQuiz,
                showDiagnosticFeedback,
                diagnosticQuestionIndex,
                diagnosticTotalQuestions
              })}
              <DiagnosticTest
                isDiagnosticMode={isDiagnosticMode}
                currentQuiz={currentDiagnosticQuiz}
                showDiagnosticFeedback={showDiagnosticFeedback}
                diagnosticFeedback={diagnosticFeedback}
                diagnosticQuestionIndex={diagnosticQuestionIndex}
                diagnosticTotalQuestions={diagnosticTotalQuestions}
                onDiagnosticQuizAnswer={onDiagnosticQuizAnswer}
                onCompleteDiagnosticTest={onCompleteDiagnosticTest}
                onNextDiagnosticQuestion={() => {
                  if (setDiagnosticState && setShowDiagnosticFeedback && setDiagnosticFeedback && diagnosticState) {
                    handleNextDiagnosticQuestion(diagnosticState, { setDiagnosticState, setShowDiagnosticFeedback, setDiagnosticFeedback });
                  }
                }}
              />
            </>
          )}
        </div>
        
        {/* Help Section */}
        {/* <div className="diagnostic-help">
          <div className="help-content">
            <div className="help-icon">💡</div>
            <div className="help-text">
              <p><strong>Tip:</strong> Use the floating button to return to course selection anytime.</p>
            </div>
          </div>
        </div> */}
      </div>
    );
  };

  const renderCourseContentPage = () => {
    console.log('🔍 Rendering course content page:', {
      currentCourse,
      currentCoursePage,
      courseGenerating
    });
    
    return (
      <div className="course-content-page">
        <div className="course-header">
          <h3>📖 {currentCourse?.title || 'Course Content'}</h3>
          {currentCourse && (
            <div className="course-progress">
              <span>Page {currentCoursePage?.pageNumber || 1} of {currentCoursePage?.totalPages || 1}</span>
            </div>
          )}
        </div>
        
        {courseGenerating ? (
          <div className="course-loading">
            <ShimmerLoading type="course" theme={theme} />
          </div>
        ) : currentCoursePage ? (
          <CoursePageComponent
            currentCoursePage={currentCoursePage}
            onNavigateCoursePage={onNavigateCoursePage}
            onCompleteCourse={onCompleteCourse}
          />
        ) : (
          <div className="course-loading-error">
            <h4>📚 Course Content Loading</h4>
            <p>Fetching your personalized course content...</p>
            <div className="loading-spinner">⏳</div>
          </div>
        )}
        
        <div className="course-navigation">
          <div className="course-info">
            <p>💡 <strong>Tip:</strong> Use the floating button to return to course selection anytime.</p>
          </div>
        </div>
      </div>
    );
  };

  const renderCourseQuizPage = () => {
    return (
      <div className="course-quiz-page">
        <div className="quiz-header">
          <h3>📝 Course Quiz</h3>
          <p>Test your knowledge from this section</p>
        </div>
        
        {quizSubmitting ? (
          <div className="quiz-loading">
            <ShimmerLoading type="quiz" theme={theme} />
          </div>
        ) : (
          <CourseQuiz
            courseQuiz={courseQuiz}
            courseQuizAnswers={courseQuizAnswers}
            onCourseQuizAnswerSelection={onCourseQuizAnswerSelection}
            onCourseQuizNavigation={onCourseQuizNavigation}
            onSubmitCourseQuiz={onSubmitCourseQuiz}
            areAllQuestionsAnswered={areAllQuestionsAnswered}
          />
        )}
        
        <div className="quiz-navigation">
          <div className="quiz-info">
            <p>💡 <strong>Tip:</strong> Use the floating button to return to course selection anytime.</p>
          </div>
        </div>
      </div>
    );
  };

  const renderCourseGenerationPage = () => {
    return (
      <div className="course-generation-page">
        {/* Modern Header Section */}
        <div className="generation-header-modern">
          <div className="header-main">
            <div className="header-icon">
              <span className="icon-large">🚀</span>
            </div>
            <div className="header-content">
              <h3 className="header-title">Generating Your Course</h3>
              <p className="header-subtitle">Creating a personalized learning experience just for you</p>
            </div>
          </div>
          
          {selectedCourseLabel && (
            <div className="course-badge">
              <span className="badge-icon">📚</span>
              <span className="badge-text">{selectedCourseLabel}</span>
            </div>
          )}
        </div>
        
        {/* Loading Animation Section */}
        <div className="generation-loading-section">
          <div className="loading-animation">
            <div className="pulse-circle"></div>
            <div className="loading-text">
              <h4>🎯 Analyzing Your Assessment Results</h4>
              <p>Understanding your knowledge level and learning preferences...</p>
            </div>
          </div>
          
          <div className="generation-steps">
            <div className="step-item completed">
              <div className="step-icon">✅</div>
              <div className="step-content">
                <h5>Assessment Complete</h5>
                <p>You've answered all diagnostic questions</p>
              </div>
            </div>
            
            <div className="step-item active">
              <div className="step-icon">🔄</div>
              <div className="step-content">
                <h5>AI Analysis</h5>
                <p>Processing your responses and performance</p>
              </div>
            </div>
            
            <div className="step-item pending">
              <div className="step-icon">📚</div>
              <div className="step-content">
                <h5>Course Creation</h5>
                <p>Building personalized learning content</p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="generation-progress">
          <div className="progress-bar">
            <div className="progress-fill"></div>
          </div>
          <p className="progress-text">This usually takes 10-15 seconds...</p>
        </div>
      </div>
    );
  };

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'courses':
        return renderCoursesPage();
      case 'diagnostic':
        return renderDiagnosticPage();
      case 'course-content':
        return renderCourseContentPage();
      case 'course-quiz':
        return renderCourseQuizPage();
      case 'course-generation':
        return renderCourseGenerationPage();
      default:
        return renderCoursesPage();
    }
  };

  return (
    <div className="learning-center">
      {renderHeader()}
      <div className="learning-center-content">
        {renderCurrentPage()}
      </div>
      {renderFloatingBackButton()}
    </div>
  );
}; 