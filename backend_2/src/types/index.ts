// Quiz Types
export interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
  correctAnswer: number;
  explanation: string;
  topicTag: string;
  difficulty: 'easy' | 'medium' | 'hard';
}

export interface QuizResponse {
  userId: string;
  timestamp: string;
  quizId: string;
  selectedOption: number;
  correct: boolean;
  topicTag: string;
  sessionId: string;
}

export interface QuizSession {
  userId: string;
  sessionId: string;
  messageCount: number;
  quizAttempts: number;
  startTime: string;
  lastActivity: string;
  completedPreTest: boolean;
  confidenceRating?: number;
}

export interface DiagnosticTest {
  questions: QuizQuestion[];
  totalQuestions: number;
  passingScore: number;
}

export type QuizType = 'diagnostic' | 'micro' | 'review' | 'course';

// Course Types
export interface CoursePage {
  id: string;
  title: string;
  content: string;
  pageNumber: number;
  totalPages: number;
}

export interface Course {
  id: string;
  title: string;
  description: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  topicTag: string;
  estimatedTime: string;
  pages: CoursePage[];
  quizQuestions: QuizQuestion[];
  prerequisites?: string[];
}

export interface CourseProgress {
  userId: string;
  sessionId: string;
  courseId: string;
  currentPageIndex: number;
  completed: boolean;
  quizAttempts: number;
  quizScore?: number;
  startTime: string;
  completionTime?: string;
}

export interface CourseSession {
  userId: string;
  sessionId: string;
  activeCourse?: Course;
  currentPageIndex: number;
  courseProgress: Map<string, CourseProgress>;
  mode: 'chat' | 'course';
}

// Chat Types
export interface ChatMessage {
  id: string;
  content: string;
  type: 'user' | 'assistant' | 'system' | 'quiz' | 'calculation' | 'course' | 'course-list';
  timestamp: string;
  sessionId: string;
  userId: string;
  metadata?: {
    quizQuestion?: QuizQuestion;
    calculationResult?: CalculationResult;
    requiresDisclaimer?: boolean;
    coursePage?: CoursePage;
    courseList?: Course[];
    courseQuiz?: {
      questions: QuizQuestion[];
      currentQuestion: number;
      score: number;
      attempts: number;
    };
  };
}

export interface ChatResponse {
  responseText: string;
  quizQuestion?: QuizQuestion;
  calculationResult?: CalculationResult;
  requiresDisclaimer?: boolean;
  coursePage?: CoursePage;
  courseList?: Course[];
  courseQuiz?: {
    questions: QuizQuestion[];
    currentQuestion: number;
    score: number;
    attempts: number;
  };
  sessionId: string;
  messageId: string;
}

export interface EngagementMetrics {
  userId: string;
  sessionId: string;
  messagesPerSession: number;
  sessionDuration: number;
  quizzesAttempted: number;
  preTestCompleted: boolean;
  lastActivity: string;
  confidenceRating?: number;
}

// Calculation Types
export type CalculationType = 'credit_card_payoff' | 'savings_goal' | 'loan_amortization';

export interface CalculationInput {
  type: CalculationType;
  inputs: {
    principal?: number;
    interestRate?: number; // APR as percentage
    monthlyPayment?: number;
    targetAmount?: number;
    timeframe?: number; // in months
    currentSavings?: number;
  };
}

export interface CalculationResult {
  type: CalculationType;
  monthlyPayment?: number;
  monthsToPayoff?: number;
  totalInterest: number;
  totalAmount: number;
  stepByStepPlan: string[];
  disclaimer: string;
  metadata: {
    inputValues: Record<string, number>;
    calculationDate: string;
  };
}

// API Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface ChatApiRequest {
  userId: string;
  message: string;
  sessionId?: string;
}

export interface ChatApiResponse extends ApiResponse {
  data: {
    responseText: string;
    quizQuestion?: QuizQuestion;
    calculationResult?: CalculationResult;
    requiresDisclaimer?: boolean;
    coursePage?: CoursePage;
    courseList?: Course[];
    courseQuiz?: {
      questions: QuizQuestion[];
      currentQuestion: number;
      score: number;
      attempts: number;
    };
    sessionId: string;
    messageId: string;
  };
}

export interface QuizLogRequest {
  userId: string;
  timestamp: string;
  quizId: string;
  selectedOption: number;
  correct: boolean;
  topicTag: string;
  sessionId: string;
}

export interface QuizLogResponse extends ApiResponse {
  data?: {
    logged: boolean;
    timestamp: string;
    logId?: string;
  };
}

export interface AnalyticsRequest {
  userId?: string;
  sessionId?: string;
  action?: string;
  startDate?: string;
  endDate?: string;
  metadata?: Record<string, any>;
}

export interface AnalyticsQueryParams {
  userId?: string;
  sessionId?: string;
  startDate?: string;
  endDate?: string;
}

export interface AnalyticsResponse extends ApiResponse {
  data?: any;
}

// Constants
export const QUIZ_CONFIG = {
  MICRO_QUIZ_INTERVAL: 5,
  DIAGNOSTIC_QUESTIONS_COUNT: 3, // Updated to 3 for diagnostic
  COURSE_QUIZ_QUESTIONS: 3,
  PASSING_SCORE_PERCENTAGE: 70,
  QUIZ_TIMEOUT_MS: 30000,
} as const;

export const CALC_DEFAULTS = {
  MIN_PAYMENT_AMOUNT: 1,
  MAX_PAYMENT_AMOUNT: 100000,
  MIN_INTEREST_RATE: 0,
  MAX_INTEREST_RATE: 50,
  MIN_PRINCIPAL: 1,
  MAX_PRINCIPAL: 10000000,
  DEFAULT_CREDIT_CARD_APR: 18.99,
  DEFAULT_SAVINGS_RATE: 2.5,
} as const;

export const QUIZ_TOPICS = {
  BUDGETING: 'budgeting',
  INVESTING: 'investing',
  DEBT_MANAGEMENT: 'debt_management',
  SAVINGS: 'savings',
  RETIREMENT: 'retirement',
  CREDIT_CARDS: 'credit_cards',
  LOANS: 'loans',
  INSURANCE: 'insurance',
  TAXES: 'taxes',
  EMERGENCY_FUND: 'emergency_fund',
} as const;

// Validation Functions
export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const validateUserId = (userId: string): boolean => {
  return typeof userId === 'string' && userId.length > 0 && userId.length <= 100;
};

export const validateMessage = (message: string): boolean => {
  return typeof message === 'string' && message.trim().length > 0 && message.length <= 1000;
};

export const validateQuizResponse = (response: any): boolean => {
  return (
    typeof response === 'object' &&
    validateUserId(response.userId) &&
    typeof response.sessionId === 'string' &&
    typeof response.quizId === 'string' &&
    typeof response.selectedOption === 'number' &&
    typeof response.correct === 'boolean' &&
    typeof response.topicTag === 'string'
  );
};

export const validateCalculationInput = (input: any): boolean => {
  if (!input || typeof input !== 'object') return false;
  
  const validTypes = ['credit_card_payoff', 'savings_goal', 'loan_amortization'];
  if (!validTypes.includes(input.type)) return false;
  
  if (!input.inputs || typeof input.inputs !== 'object') return false;
  
  for (const [key, value] of Object.entries(input.inputs)) {
    if (value !== undefined && (typeof value !== 'number' || isNaN(value) || value < 0)) {
      return false;
    }
  }
  
  return true;
}; 