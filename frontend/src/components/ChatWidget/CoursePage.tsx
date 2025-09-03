import React from 'react';
import { BookOpen, ChevronLeft, ChevronRight, CheckCircle } from 'lucide-react';
import '../../styles/ChatWidget.css';
import { CoursePage as CoursePageType } from '../../types';
import { renderMarkdown } from '../../utils/chatWidget';

interface CoursePageProps {
  currentCoursePage: CoursePageType | null;
  onNavigateCoursePage: (pageIndex: number) => void;
  onCompleteCourse: () => void;
}

export const CoursePage: React.FC<CoursePageProps> = ({
  currentCoursePage,
  onNavigateCoursePage,
  onCompleteCourse
}) => {
  if (!currentCoursePage) {
    return null;
  }

  return (
    <div className="course-page-container">
      <div className="course-page-header">
        <div className="course-page-title">
          <BookOpen size={18} />
          <h3>{currentCoursePage.title}</h3>
        </div>
        <div className="course-page-progress">
          Page {currentCoursePage.pageNumber} of {currentCoursePage.totalPages}
        </div>
      </div>
      
      <div className="course-page-content">
        {renderMarkdown(currentCoursePage.content)}
      </div>
      
      <div className="course-page-navigation">
        <button
          onClick={() => onNavigateCoursePage(currentCoursePage.pageNumber - 2)}
          disabled={currentCoursePage.pageNumber === 1}
          className="course-nav-btn course-nav-prev"
        >
          <ChevronLeft size={16} />
          Previous
        </button>
        
        <div className="course-page-indicator">
          {Array.from({ length: currentCoursePage.totalPages }, (_, i) => (
            <div
              key={i}
              className={`page-dot ${i + 1 === currentCoursePage.pageNumber ? 'active' : ''}`}
              onClick={() => onNavigateCoursePage(i)}
            />
          ))}
        </div>
        
        {currentCoursePage.pageNumber < currentCoursePage.totalPages ? (
          <button
            onClick={() => onNavigateCoursePage(currentCoursePage.pageNumber)}
            className="course-nav-btn course-nav-next"
          >
            Next
            <ChevronRight size={16} />
          </button>
        ) : (
          <button
            onClick={onCompleteCourse}
            className="course-nav-btn course-complete-btn"
          >
            <CheckCircle size={16} />
            Complete Course
          </button>
        )}
      </div>
    </div>
  );
}; 