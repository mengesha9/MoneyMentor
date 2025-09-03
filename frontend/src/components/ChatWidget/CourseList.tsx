import React from 'react';
import { BookOpen, Play } from 'lucide-react';
import '../../styles/ChatWidget.css';
import { Course } from '../../types';

interface CourseListProps {
  showCourseList: boolean;
  availableCourses: Course[];
  onStartCourse: (courseId: string) => void;
}

export const CourseList: React.FC<CourseListProps> = ({
  showCourseList,
  availableCourses,
  onStartCourse
}) => {
  if (!showCourseList || availableCourses.length === 0) {
    return null;
  }

  return (
    <div className="course-list-container">
      <div className="course-list-header">
        <BookOpen size={20} />
        <h3>Available Courses</h3>
      </div>
      
      <div className="courses-grid">
        {availableCourses.map((course) => (
          <div key={course.id} className="course-card">
            <div className="course-card-header">
              <h4 className="course-title">{course.title}</h4>
              <span className={`difficulty-badge ${course.difficulty}`}>
                {course.difficulty}
              </span>
            </div>
            
            <p className="course-description">{course.description}</p>
            
            <div className="course-meta">
              <span className="course-time">⏱️ {course.estimatedTime}</span>
              <span className="course-pages">📄 {course.pages.length} pages</span>
            </div>
            
            <button 
              onClick={() => onStartCourse(course.id)}
              className="start-course-btn"
            >
              <Play size={16} />
              Start Course
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}; 