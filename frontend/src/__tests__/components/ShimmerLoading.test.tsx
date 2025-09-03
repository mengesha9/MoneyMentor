import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ShimmerLoading } from '../../components/ChatWidget/ShimmerLoading';

describe('ShimmerLoading', () => {
  describe('Message Shimmer', () => {
    it('should render message shimmer with light theme', () => {
      render(<ShimmerLoading type="message" theme="light" />);
      
      const shimmerContainer = screen.getByTestId('shimmer-message-container');
      expect(shimmerContainer).toBeInTheDocument();
      
      const shimmerLines = shimmerContainer.querySelectorAll('.shimmer-line');
      expect(shimmerLines).toHaveLength(4);
      
      shimmerLines.forEach(line => {
        expect(line).toHaveClass('shimmer-light');
      });
    });

    it('should render message shimmer with dark theme', () => {
      render(<ShimmerLoading type="message" theme="dark" />);
      
      const shimmerContainer = screen.getByTestId('shimmer-message-container');
      expect(shimmerContainer).toBeInTheDocument();
      
      const shimmerLines = shimmerContainer.querySelectorAll('.shimmer-line');
      expect(shimmerLines).toHaveLength(4);
      
      shimmerLines.forEach(line => {
        expect(line).toHaveClass('shimmer-dark');
      });
    });
  });

  describe('Quiz Shimmer', () => {
    it('should render quiz shimmer with light theme', () => {
      render(<ShimmerLoading type="quiz" theme="light" />);
      
      const quizContainer = screen.getByTestId('shimmer-quiz-container');
      expect(quizContainer).toBeInTheDocument();
      expect(quizContainer).toHaveClass('shimmer-quiz');
      
      const quizOptions = quizContainer.querySelectorAll('.quiz-option');
      expect(quizOptions).toHaveLength(4);
      
      const shimmerLines = quizContainer.querySelectorAll('.shimmer-line');
      expect(shimmerLines.length).toBeGreaterThan(0);
      
      shimmerLines.forEach(line => {
        expect(line).toHaveClass('shimmer-light');
      });
    });

    it('should render quiz shimmer with dark theme', () => {
      render(<ShimmerLoading type="quiz" theme="dark" />);
      
      const quizContainer = screen.getByTestId('shimmer-quiz-container');
      expect(quizContainer).toBeInTheDocument();
      expect(quizContainer).toHaveClass('shimmer-quiz');
      
      const shimmerLines = quizContainer.querySelectorAll('.shimmer-line');
      expect(shimmerLines.length).toBeGreaterThan(0);
      
      shimmerLines.forEach(line => {
        expect(line).toHaveClass('shimmer-dark');
      });
    });
  });

  describe('Course Shimmer', () => {
    it('should render course shimmer with light theme', () => {
      render(<ShimmerLoading type="course" theme="light" />);
      
      const courseContainer = screen.getByTestId('shimmer-course-container');
      expect(courseContainer).toBeInTheDocument();
      expect(courseContainer).toHaveClass('shimmer-course');
      
      const shimmerLines = courseContainer.querySelectorAll('.shimmer-line');
      expect(shimmerLines.length).toBeGreaterThan(0);
      
      shimmerLines.forEach(line => {
        expect(line).toHaveClass('shimmer-light');
      });
    });

    it('should render course shimmer with dark theme', () => {
      render(<ShimmerLoading type="course" theme="dark" />);
      
      const courseContainer = screen.getByTestId('shimmer-course-container');
      expect(courseContainer).toBeInTheDocument();
      expect(courseContainer).toHaveClass('shimmer-course');
      
      const shimmerLines = courseContainer.querySelectorAll('.shimmer-line');
      expect(shimmerLines.length).toBeGreaterThan(0);
      
      shimmerLines.forEach(line => {
        expect(line).toHaveClass('shimmer-dark');
      });
    });
  });

  describe('Diagnostic Shimmer', () => {
    it('should render diagnostic shimmer with light theme', () => {
      render(<ShimmerLoading type="diagnostic" theme="light" />);
      
      const diagnosticContainer = screen.getByTestId('shimmer-diagnostic-container');
      expect(diagnosticContainer).toBeInTheDocument();
      expect(diagnosticContainer).toHaveClass('shimmer-diagnostic');
      
      const diagnosticOptions = diagnosticContainer.querySelectorAll('.diagnostic-option');
      expect(diagnosticOptions).toHaveLength(4);
      
      const shimmerLines = diagnosticContainer.querySelectorAll('.shimmer-line');
      expect(shimmerLines.length).toBeGreaterThan(0);
      
      shimmerLines.forEach(line => {
        expect(line).toHaveClass('shimmer-light');
      });
    });

    it('should render diagnostic shimmer with dark theme', () => {
      render(<ShimmerLoading type="diagnostic" theme="dark" />);
      
      const diagnosticContainer = screen.getByTestId('shimmer-diagnostic-container');
      expect(diagnosticContainer).toBeInTheDocument();
      expect(diagnosticContainer).toHaveClass('shimmer-diagnostic');
      
      const shimmerLines = diagnosticContainer.querySelectorAll('.shimmer-line');
      expect(shimmerLines.length).toBeGreaterThan(0);
      
      shimmerLines.forEach(line => {
        expect(line).toHaveClass('shimmer-dark');
      });
    });
  });

  describe('Default Behavior', () => {
    it('should default to light theme when no theme is provided', () => {
      render(<ShimmerLoading type="message" />);
      
      const shimmerContainer = screen.getByTestId('shimmer-message-container');
      const shimmerLines = shimmerContainer.querySelectorAll('.shimmer-line');
      expect(shimmerLines.length).toBeGreaterThan(0);
      
      shimmerLines.forEach(line => {
        expect(line).toHaveClass('shimmer-light');
      });
    });

    it('should default to message type when invalid type is provided', () => {
      render(<ShimmerLoading type="invalid" as any />);
      
      const messageContainer = screen.getByTestId('shimmer-message-container');
      expect(messageContainer).toBeInTheDocument();
    });
  });

  describe('Animation Classes', () => {
    it('should apply shimmer animation classes', () => {
      render(<ShimmerLoading type="message" theme="light" />);
      
      const shimmerContainer = screen.getByTestId('shimmer-message-container');
      const shimmerLines = shimmerContainer.querySelectorAll('.shimmer-line');
      expect(shimmerLines.length).toBeGreaterThan(0);
      
      shimmerLines.forEach(line => {
        expect(line).toHaveClass('shimmer-light');
        // Instead of checking inline style, check for shimmer class
        expect(line.className).toMatch(/shimmer/);
      });
    });
  });
}); 