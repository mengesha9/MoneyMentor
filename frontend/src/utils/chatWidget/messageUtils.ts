import { ChatMessage, CalculationResult } from '../../types';
import { v4 as uuidv4 } from 'uuid';

/**
 * Create a new chat message
 */
export const createMessage = (
  content: string,
  type: 'user' | 'assistant' | 'system',
  sessionId: string,
  userId: string
): ChatMessage => ({
  id: uuidv4(),
  content,
  type,
  timestamp: new Date().toISOString(),
  sessionId,
  userId
});

/**
 * Create a user message
 */
export const createUserMessage = (
  content: string,
  sessionId: string,
  userId: string
): ChatMessage => createMessage(content, 'user', sessionId, userId);

/**
 * Create an assistant message
 */
export const createAssistantMessage = (
  content: string,
  sessionId: string,
  userId: string
): ChatMessage => createMessage(content, 'assistant', sessionId, userId);

/**
 * Create a system message
 */
export const createSystemMessage = (
  content: string,
  sessionId: string,
  userId: string
): ChatMessage => createMessage(content, 'system', sessionId, userId);

/**
 * Create a welcome message
 */
export const createWelcomeMessage = (
  sessionId: string,
  userId: string
): ChatMessage => {
  const welcomeContent = `👋 **Welcome to MoneyMentor!**

I'm your AI financial advisor, here to help you build better money habits and achieve your financial goals.

**What I can help you with:**
• 💰 **Budgeting & Saving** - Create budgets and savings plans
• 📊 **Investment Guidance** - Learn about investing basics
• 💳 **Debt Management** - Strategies to pay off debt faster
• 🎯 **Financial Goals** - Plan for major purchases or retirement
• 📚 **Financial Education** - Take courses and quizzes

**Try these commands:**
• \`diagnostic_test\` - Take a quick assessment of your financial knowledge
• \`courses\` - Browse available financial education courses
• \`chat\` - Start a general conversation about money

What would you like to work on today?`;

  return createSystemMessage(welcomeContent, sessionId, userId);
};

/**
 * Create a calculation result message
 */
export const createCalculationMessage = (
  result: CalculationResult,
  sessionId: string,
  userId: string
): ChatMessage => ({
  id: uuidv4(),
  content: '',
  type: 'calculation',
  timestamp: new Date().toISOString(),
  sessionId,
  userId,
  metadata: {
    calculationResult: result
  }
});

/**
 * Format content for display
 */
export const formatContent = (content: string): string => {
  // Convert markdown-style formatting to HTML
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>');
};

/**
 * Format file upload success message
 */
export const formatUploadSuccessMessage = (fileName: string): string => 
  `✅ Successfully uploaded "${fileName}". I can now answer questions about this content!`;

/**
 * Format file upload error message
 */
export const formatUploadErrorMessage = (fileName: string, error: string): string => 
  `❌ Failed to upload "${fileName}": ${error}`;

/**
 * Format file removal message
 */
export const formatFileRemovalMessage = (fileName: string): string => 
  `🗑️ Removed "${fileName}" from your knowledge base.`;

/**
 * Format course start message
 */
export const formatCourseStartMessage = (courseTitle: string): string => 
  `📚 Started course: **${courseTitle}**`;

/**
 * Format course completion message
 */
export const formatCourseCompletionMessage = (): string => 
  '🎯 Course completed! Time for the quiz.';

import React from 'react';

/**
 * Render markdown content for display
 */
export const renderMarkdown = (content: string): React.ReactElement[] => {
  return content.split('\n').map((line, index) => {
    // Handle headers
    if (line.startsWith('# ')) {
      return React.createElement('h1', { key: index, className: 'course-h1' }, line.substring(2));
    }
    if (line.startsWith('## ')) {
      return React.createElement('h2', { key: index, className: 'course-h2' }, line.substring(3));
    }
    if (line.startsWith('### ')) {
      return React.createElement('h3', { key: index, className: 'course-h3' }, line.substring(4));
    }
    
    // Handle bold text **text**
    if (line.includes('**')) {
      const parts = line.split('**');
      return React.createElement('p', { key: index, className: 'course-paragraph' },
        parts.map((part, partIndex) => 
          partIndex % 2 === 1 ? React.createElement('strong', { key: partIndex }, part) : part
        )
      );
    }
    
    // Handle bullet points
    if (line.trim().startsWith('•')) {
      return React.createElement('li', { key: index, className: 'course-bullet' }, line.trim().substring(1).trim());
    }
    
    // Handle numbered lists
    if (/^\d+\./.test(line.trim())) {
      return React.createElement('li', { key: index, className: 'course-numbered' }, line.trim());
    }
    
    // Empty line
    if (line.trim() === '') {
      return React.createElement('br', { key: index });
    }
    
    // Regular paragraph
    return React.createElement('p', { key: index, className: 'course-paragraph' }, line);
  });
};

/**
 * Format message content for display in chat
 */
export const formatMessageContent = (
  content: string
): React.ReactElement[] => {
  return content.split('\n').map((line, index) => {
    // Handle bold text **text**
    if (line.includes('**')) {
      const parts = line.split(/(\*\*[^*]+\*\*)/g);
      return React.createElement('div', { key: index },
        parts.map((part, partIndex) => {
          // Handle bold text
          if (part.startsWith('**') && part.endsWith('**')) {
            return React.createElement('strong', { key: partIndex }, part.slice(2, -2));
          }
          return part;
        })
      );
    }
    // Handle bullet points
    if (line.trim().startsWith('•')) {
      return React.createElement('div', { key: index, className: 'bullet-point' }, line);
    }
    // Handle horizontal rule
    if (line.trim() === '---') {
      return React.createElement('hr', { key: index, className: 'message-divider' });
    }
    // Regular line
    return React.createElement('div', { key: index }, line || React.createElement('br'));
  });
};

/**
 * Convert snake_case calculation result from API to camelCase for frontend
 */
export const convertCalculationResult = (apiResult: any): CalculationResult => {
  return {
    type: apiResult.type || 'financial_calculation',
    monthlyPayment: apiResult.monthly_payment,
    monthsToPayoff: apiResult.months_to_payoff,
    totalInterest: apiResult.total_interest,
    totalAmount: apiResult.total_amount,
    stepByStepPlan: apiResult.step_by_step_plan || [],
    disclaimer: apiResult.disclaimer || 'Estimates only. Verify with a certified financial professional.',
    metadata: {
      inputValues: apiResult.metadata?.input_values || {},
      calculationDate: apiResult.metadata?.calculation_date || new Date().toISOString()
    }
  };
}; 