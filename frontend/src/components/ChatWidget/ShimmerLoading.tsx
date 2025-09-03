import React from 'react';
import '../../styles/ChatWidget.css';

interface ShimmerLoadingProps {
  type: 'message' | 'quiz' | 'course' | 'diagnostic';
  theme?: 'light' | 'dark';
}

export const ShimmerLoading: React.FC<ShimmerLoadingProps> = ({ 
  type, 
  theme = 'light' 
}) => {
  const shimmerClass = theme === 'dark' ? 'shimmer-dark' : 'shimmer-light';

  const renderMessageShimmer = () => (
    <div className="message assistant group">
      <div className="message-content">
        <div className="shimmer-message-container" data-testid="shimmer-message-container">
          <div className={`shimmer-line ${shimmerClass}`} style={{ width: '90%', height: '16px' }}></div>
          <div className={`shimmer-line ${shimmerClass}`} style={{ width: '85%', height: '16px' }}></div>
          <div className={`shimmer-line ${shimmerClass}`} style={{ width: '70%', height: '16px' }}></div>
          <div className={`shimmer-line ${shimmerClass}`} style={{ width: '60%', height: '16px' }}></div>
        </div>
      </div>
    </div>
  );

  const renderQuizShimmer = () => (
    <div className="quiz-container shimmer-quiz" data-testid="shimmer-quiz-container">
      <div className="quiz-header">
        <div className={`shimmer-line ${shimmerClass}`} style={{ width: '200px', height: '20px', marginBottom: '16px' }}></div>
        <div className={`shimmer-line ${shimmerClass}`} style={{ width: '150px', height: '14px' }}></div>
      </div>
      <div className="quiz-question">
        <div className={`shimmer-line ${shimmerClass}`} style={{ width: '90%', height: '18px', marginBottom: '20px' }}></div>
      </div>
      <div className="quiz-options">
        {[0, 1, 2, 3].map((index) => (
          <div key={index} className="quiz-option shimmer-option">
            <div className="option-indicator">
              <div className={`shimmer-line ${shimmerClass}`} style={{ width: '20px', height: '20px' }}></div>
            </div>
            <div className={`shimmer-line ${shimmerClass}`} style={{ width: '100%', height: '16px' }}></div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderCourseShimmer = () => (
    <div className="course-container shimmer-course" data-testid="shimmer-course-container">
      <div className="course-header">
        <div className={`shimmer-line ${shimmerClass}`} style={{ width: '250px', height: '24px', marginBottom: '12px' }}></div>
        <div className={`shimmer-line ${shimmerClass}`} style={{ width: '180px', height: '16px', marginBottom: '20px' }}></div>
      </div>
      <div className="course-content">
        <div className={`shimmer-line ${shimmerClass}`} style={{ width: '100%', height: '16px', marginBottom: '12px' }}></div>
        <div className={`shimmer-line ${shimmerClass}`} style={{ width: '95%', height: '16px', marginBottom: '12px' }}></div>
        <div className={`shimmer-line ${shimmerClass}`} style={{ width: '85%', height: '16px', marginBottom: '12px' }}></div>
        <div className={`shimmer-line ${shimmerClass}`} style={{ width: '90%', height: '16px', marginBottom: '12px' }}></div>
        <div className={`shimmer-line ${shimmerClass}`} style={{ width: '75%', height: '16px' }}></div>
      </div>
      <div className="course-navigation">
        <div className={`shimmer-line ${shimmerClass}`} style={{ width: '120px', height: '40px', borderRadius: '8px' }}></div>
      </div>
    </div>
  );

  const renderDiagnosticShimmer = () => (
    <div className="diagnostic-container shimmer-diagnostic" data-testid="shimmer-diagnostic-container">
      <div className="diagnostic-header">
        <div className="diagnostic-progress">
          <div className="progress-circle">
            <div className={`shimmer-line ${shimmerClass}`} style={{ width: '24px', height: '24px', borderRadius: '50%' }}></div>
            <div className={`shimmer-line ${shimmerClass}`} style={{ width: '20px', height: '12px' }}></div>
          </div>
        </div>
      </div>
      <div className="diagnostic-question">
        <div className={`shimmer-line ${shimmerClass}`} style={{ width: '90%', height: '20px', marginBottom: '16px' }}></div>
      </div>
      <div className="diagnostic-options">
        {[0, 1, 2, 3].map((index) => (
          <div key={index} className="diagnostic-option shimmer-option">
            <div className="option-indicator">
              <div className={`shimmer-line ${shimmerClass}`} style={{ width: '20px', height: '20px' }}></div>
            </div>
            <div className={`shimmer-line ${shimmerClass}`} style={{ width: '100%', height: '16px' }}></div>
          </div>
        ))}
      </div>
    </div>
  );

  switch (type) {
    case 'message':
      return renderMessageShimmer();
    case 'quiz':
      return renderQuizShimmer();
    case 'course':
      return renderCourseShimmer();
    case 'diagnostic':
      return renderDiagnosticShimmer();
    default:
      return renderMessageShimmer();
  }
}; 