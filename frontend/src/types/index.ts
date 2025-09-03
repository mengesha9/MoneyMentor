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
  quiz_id: string;
  selected_option: string;
  correct: boolean;
  topic: string;
}

export interface QuizFeedback {
  correct: boolean;
  explanation: string;
}

// Chat Types
export interface ChatMessage {
  id: string;
  content: string;
  type: 'user' | 'assistant' | 'system' | 'quiz' | 'calculation' | 'course' | 'course-list' | 'welcome';
  timestamp: string;
  sessionId: string;
  userId: string;
  metadata?: {
    buttons?: {
      label: string;
      action: () => void;
    }[];
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
  message: string;
  session_id: string;
  quiz: QuizQuestion | null;
  is_calculation?: boolean;
  calculation_result?: {
    type?: string;
    monthly_payment?: number;
    months_to_payoff?: number;
    total_interest: number;
    total_amount: number;
    step_by_step_plan?: string[];
    disclaimer?: string;
    metadata?: {
      input_values?: Record<string, number>;
      calculation_date?: string;
    };
  };
}

export interface DiagnosticTest {
  questions: QuizQuestion[];
  totalQuestions: number;
  passingScore: number;
}

export interface QuizSession {
  userId: string;
  sessionId: string;
  messageCount: number;
  quizAttempts: number;
  startTime: string;
  lastActivity: string;
  completedPreTest: boolean;
}

// Course Types
export interface CoursePage {
  id: string;
  title: string;
  content: string;
  pageNumber: number;
  totalPages: number;
  pageType?: string;
  quizData?: any;
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

// Calculation Types
export interface CalculationResult {
  type: string;
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

// Local Storage Keys
export const STORAGE_KEYS = {
  USER_ID: 'moneymentor_user_id', // Updated to match the key used in session management
  SESSION_ID: 'moneymentor_session_id',
  QUIZ_PROGRESS: 'moneymentor_quiz_progress',
  CHAT_HISTORY: 'moneymentor_chat_history',
  PREFERENCES: 'moneymentor_preferences',
} as const;

// Sidebar types
export interface SidebarState {
  isOpen: boolean;
  isCollapsed: boolean;
  selectedSessionId: string | null;
}

// User Profile types
export interface UserProfile {
  id: string;
  name: string;
  email: string;
  avatar: string;
  joinDate: string;
  subscription: 'free' | 'premium';
  totalChats: number;
  totalQuizzes: number;
  streakDays: number;
  preferences: {
    theme: 'light' | 'dark';
    notifications: boolean;
    autoSave: boolean;
  };
}

// Chat Session types
export interface ChatSession {
  id: string;
  title: string;
  preview: string;
  timestamp: string;
  messageCount: number;
  lastActivity: string;
  tags: string[];
  isActive?: boolean;
}

// Profile Modal types
export interface ProfileModalState {
  isOpen: boolean;
  activeTab: 'profile' | 'settings' | 'quizzes';
}

// Sidebar handlers props
export interface SidebarHandlersProps {
  sidebarState: SidebarState;
  setSidebarState: (state: SidebarState) => void;
  onSessionSelect: (sessionId: string) => void;
  onNewChat: () => void;
}

// Profile handlers props
export interface ProfileHandlersProps {
  profileModalState: ProfileModalState;
  setProfileModalState: (state: ProfileModalState) => void;
  userProfile: UserProfile;
  onProfileUpdate: (profile: Partial<UserProfile>) => void;
} 