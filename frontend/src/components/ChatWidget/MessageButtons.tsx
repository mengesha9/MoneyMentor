import React from 'react';
import '../../styles/ChatWidget.css';

interface MessageButtonsProps {
  buttons: {
    label: string;
    action: () => void;
  }[];
  className?: string;
  messageId?: string;
}

export const MessageButtons: React.FC<MessageButtonsProps> = ({ buttons, className = '', messageId }) => {
  if (!buttons || buttons.length === 0) return null;

  // Check if this is the learning course selection message
  const isLearningCourseSelection = messageId === 'learn-courses-list';

  // Define colors and icons for each course topic
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

  if (isLearningCourseSelection) {
    return (
      <div className="learning-topic-buttons">
        {buttons.map((button, index) => {
          const style = getTopicStyle(button.label);
          // Get description for the course
          const getDescription = (label: string) => {
            switch (label) {
              case 'Money, Goals and Mindset':
                return 'Learn to set smart financial goals and develop a positive money mindset for your future';
              case 'Budgeting and Saving':
                return 'Master budgeting basics and build healthy saving habits for financial success';
              case 'College Planning and Saving':
                return 'Plan for college costs, find scholarships, and learn about student loans';
              case 'Earning and Income Basics':
                return 'Understand paychecks, first jobs, and smart money habits when you start earning';
              default:
                return '';
            }
          };
          
          return (
            <button
              key={index}
              className="learning-topic-button"
              onClick={button.action}
              style={{ background: style.gradient }}
            >
              <div className="topic-content">
                <span className="topic-icon">{style.icon}</span>
                <div className="topic-text">
                  <span className="topic-label">{button.label}</span>
                  <span className="topic-description">{getDescription(button.label)}</span>
                </div>
              </div>
              <span className="topic-arrow">→</span>
            </button>
          );
        })}
      </div>
    );
  }

  // Default message buttons for other use cases
  return (
    <div className={`message-buttons ${className}`}>
      {buttons.map((button, index) => (
        <button
          key={index}
          className="message-button"
          onClick={button.action}
        >
          {button.label}
        </button>
      ))}
    </div>
  );
}; 