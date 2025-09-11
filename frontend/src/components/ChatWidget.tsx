import React, { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import SessionExpiredModal from './SessionExpiredModal';
import Cookies from 'js-cookie';
import { logout } from './AuthModal';
import { LogoutRounded } from '@mui/icons-material';

import { 
  ChatMessage, 
  QuizQuestion,
  Course,
  CoursePage,
  ChatSession,
  UserProfile,
  ChatResponse
} from '../types';

// Import ChatWidget components
import { 
  DiagnosticTest, 
  Quiz, 
  CourseList, 
  CoursePage as CoursePageComponent, 
  CourseQuiz,
  UploadProgressIndicator,
  UploadedFilesDisplay,
  ChatInput,
  CalculationResult,
  MessageButtons,
  QuizHistoryDropdown,
  BotMessage,
  ShimmerLoading
} from './ChatWidget/index';

// Import LearningCenter component
import { LearningCenter, LearningPage } from './ChatWidget/LearningCenter';

// Import Windows component
import { Windows } from './Windows';

// Import Sidebar components
import { Sidebar, SidebarToggle } from './Sidebar';
import { LandingPage } from './LandingPage';

// Import logic handlers
import {
  handleSendMessage,
  handleStartDiagnosticTest,
  handleDiagnosticQuizAnswer,
  handleNextDiagnosticQuestion,
  handleCompleteDiagnosticTest,
  handleCoursesList,
  handleStartCourse,
  handleNavigateCoursePage,
  handleCompleteCourse,
  handleSubmitCourseQuiz,
  handleQuizAnswer,
  handleFileUpload,
  handleRemoveFile,
  MessageHandlersProps,
  DiagnosticHandlersProps,
  CourseHandlersProps,
  QuizHandlersProps,
  FileHandlersProps
} from '../logic';

// Import custom hooks
import { useSessionState, useScrollToBottom, useSidebar, useProfile } from '../hooks';

// Import utilities
import {
  // API utilities
  ApiConfig,
  sendChatMessageStream,
  generateDiagnosticQuiz,
  generateMicroQuiz,
  submitDiagnosticQuizAnswers,

  uploadFile,
  
  SessionIds,
  
  // Diagnostic utilities
  DiagnosticState,
  initializeDiagnosticState,
  
  // Quiz utilities
  QuizFeedback,
  CourseQuizState,
  CourseQuizAnswers,
  initializeCourseQuizAnswers,
  handleCourseQuizAnswer,
  navigateToNextQuizQuestion,
  navigateToPreviousQuizQuestion,
  navigateToQuizQuestion,
  areAllQuestionsAnswered,
 
  
  // Message utilities
  createWelcomeMessage,
  createSystemMessage,
  createUserMessage,
  createAssistantMessage,
 
  formatMessageContent,
  
  // File utilities
  validateFiles,
  UploadProgress,
  initializeUploadProgress,
  updateUploadProgress,
  resetUploadProgress,

} from '../utils/chatWidget';

// Import session utilities
import { getMockChatSessions } from '../utils/sessions';
import { getAllUserSessions, getSessionHistory, deleteSession } from '../utils/chatWidget/api';
import { setActiveSession, setNewChatSession, isNewChatSession } from '../utils/chatWidget/session';
import { isSessionExpiredOrExpiringSoon, getSessionInfo } from '../utils/sessionUtils';
import { getSessionQuizProgress, getSessionQuizHistory, getSessionChatCount } from '../utils/chatWidget/api';
import Skeleton from 'react-loading-skeleton';
import { submitMicroQuiz } from '../utils/chatWidget/api';

// Import styles
import '../styles/windows.css';
import '../styles/sidebar.css';

// Window class to encapsulate all window state and functionality
class WindowInstance {
  // Messages and input
  messages: ChatMessage[] = [];
  inputValue: string = '';
  isLoading: boolean = false;
  
  // Quiz state
  currentQuiz: QuizQuestion | null = null;
  showQuizFeedback: boolean = false;
  lastQuizAnswer: QuizFeedback | null = null;
  
  // Diagnostic state
  diagnosticState: DiagnosticState = initializeDiagnosticState();
  isDiagnosticMode: boolean = false;
  showDiagnosticFeedback: boolean = false;
  diagnosticFeedback: QuizFeedback | null = null;
  
  // Course state
  availableCourses: Course[] = [];
  currentCourse: Course | null = null;
  currentCoursePage: CoursePage | null = null;
  showCourseList: boolean = false;
  courseQuiz: CourseQuizState | null = null;
  courseQuizAnswers: CourseQuizAnswers = initializeCourseQuizAnswers(0);
  
  // File upload state (only for chat window)
  uploadedFiles: File[] = [];
  uploadProgress: UploadProgress = initializeUploadProgress();
  
  constructor(
    private apiConfig: ApiConfig,
    private sessionIds: SessionIds,
    private windowName: 'chat' | 'learn',
    private addMessage: (message: ChatMessage) => void,
    private setInputValue: (value: string) => void,
    private setIsLoading: (loading: boolean) => void,
    private setCurrentQuiz: (quiz: QuizQuestion | null) => void,
    private setShowQuizFeedback: (show: boolean) => void,
    private setLastQuizAnswer: (answer: QuizFeedback | null) => void,
    private setDiagnosticState: (state: DiagnosticState) => void,
    private setIsDiagnosticMode: (mode: boolean) => void,
    private setShowDiagnosticFeedback: (show: boolean) => void,
    private setDiagnosticFeedback: (feedback: QuizFeedback | null) => void,
    private setAvailableCourses: (courses: Course[]) => void,
    private setShowCourseList: (show: boolean) => void,
    private setCurrentCoursePage: (page: CoursePage | null) => void,
    private setCurrentCourse: (course: Course | null) => void,
    private setCourseQuiz: (quiz: CourseQuizState | null) => void,
    private setCourseQuizAnswers: (answers: CourseQuizAnswers) => void,
    private setUploadedFiles: (files: File[]) => void,
    private setUploadProgress: (progress: UploadProgress) => void,
    private removeIntroMessage: (pattern: string) => void,
    private setDiagnosticGenerating?: (loading: boolean) => void,
    private setCourseGenerating?: (loading: boolean) => void,
    private setCourseCompleting?: (loading: boolean) => void,
    private setQuizSubmitting?: (loading: boolean) => void
  ) {}
  
  // Initialize welcome message
  initializeWelcome() {
    if (this.messages.length === 0) {
      if (this.windowName === 'chat') {
        const welcomeMessage = createWelcomeMessage(
          this.sessionIds.sessionId,
          this.sessionIds.userId
        );
        this.addMessage(welcomeMessage);
      }
    }
  }
  
  // Close current displays
  closeCurrentDisplays() {
    this.setShowCourseList(false);
    this.setCurrentCoursePage(null);
    this.setCurrentCourse(null);
    this.setCurrentQuiz(null);
    this.setIsDiagnosticMode(false);
    this.setShowDiagnosticFeedback(false);
    this.setDiagnosticFeedback(null);
    this.setShowQuizFeedback(false);
    this.setLastQuizAnswer(null);
    this.setCourseQuiz(null);
    this.setCourseQuizAnswers(initializeCourseQuizAnswers(0));
    this.setDiagnosticState(initializeDiagnosticState());
    this.setAvailableCourses([]);
  }
  
  // Create message handlers props
  createMessageHandlersProps(): MessageHandlersProps {
    return {
      apiConfig: this.apiConfig,
      sessionIds: this.sessionIds,
      addMessage: this.addMessage,
      setInputValue: this.setInputValue,
      setShowCommandSuggestions: () => {},
      setCommandSuggestions: () => {},
      setShowCommandMenu: () => {},
      setIsLoading: this.setIsLoading,
      closeCurrentDisplays: this.closeCurrentDisplays.bind(this),
      handleStartDiagnosticTestWrapper: this.handleStartDiagnosticTest.bind(this),
      handleCoursesListWrapper: this.handleCoursesList.bind(this),
      setCurrentQuiz: this.setCurrentQuiz
    };
  }
  
  // Create diagnostic handlers props
  createDiagnosticHandlersProps(): DiagnosticHandlersProps {
    return {
      apiConfig: this.apiConfig,
      sessionIds: this.sessionIds,
      addMessage: this.addMessage,
      setIsLoading: this.setIsLoading,
      setDiagnosticGenerating: this.setDiagnosticGenerating,
      closeCurrentDisplays: this.closeCurrentDisplays.bind(this),
      setDiagnosticState: this.setDiagnosticState,
      setIsDiagnosticMode: this.setIsDiagnosticMode,
      setShowDiagnosticFeedback: this.setShowDiagnosticFeedback,
      setDiagnosticFeedback: this.setDiagnosticFeedback,
      removeIntroMessage: this.removeIntroMessage,
      handleCompleteDiagnosticTestWrapper: this.handleCompleteDiagnosticTest.bind(this)
    };
  }
  
  // Create course handlers props
  createCourseHandlersProps(): CourseHandlersProps {
    return {
      apiConfig: this.apiConfig,
      sessionIds: this.sessionIds,
      addMessage: this.addMessage,
      setIsLoading: this.setIsLoading,
      setCourseGenerating: this.setCourseGenerating,
      setCourseCompleting: this.setCourseCompleting,
      closeCurrentDisplays: this.closeCurrentDisplays.bind(this),
      setAvailableCourses: this.setAvailableCourses,
      setShowCourseList: this.setShowCourseList,
      setCurrentCoursePage: this.setCurrentCoursePage,
      setCurrentCourse: this.setCurrentCourse,
      setCourseQuiz: this.setCourseQuiz,
      setCourseQuizAnswers: this.setCourseQuizAnswers,
      removeIntroMessage: this.removeIntroMessage
    };
  }
  
  // Create quiz handlers props
  createQuizHandlersProps(): QuizHandlersProps {
    return {
      apiConfig: this.apiConfig,
      setLastQuizAnswer: this.setLastQuizAnswer,
      setShowQuizFeedback: this.setShowQuizFeedback,
      setCurrentQuiz: this.setCurrentQuiz,
      setQuizSubmitting: this.setQuizSubmitting
    };
  }
  
  // Create file handlers props
  createFileHandlersProps(): FileHandlersProps {
    return {
      apiConfig: this.apiConfig,
      sessionIds: this.sessionIds,
      addMessage: this.addMessage,
      setUploadedFiles: this.setUploadedFiles,
      setUploadProgress: this.setUploadProgress,
      uploadedFiles: this.uploadedFiles
    };
  }
  
  // Handle send message
  async handleSendMessage(messageText: string) {
    await handleSendMessage(messageText, this.createMessageHandlersProps());
  }
  
  // Handle start diagnostic test
  async handleStartDiagnosticTest(courseKey: string = "") {
    await handleStartDiagnosticTest(this.createDiagnosticHandlersProps(), courseKey);
  }
  
  // Handle diagnostic quiz answer
  async handleDiagnosticQuizAnswer(selectedOption: number, correct: boolean, diagnosticState: DiagnosticState) {
    await handleDiagnosticQuizAnswer(selectedOption, correct, diagnosticState, this.createDiagnosticHandlersProps());
  }
  
  // Handle complete diagnostic test
  async handleCompleteDiagnosticTest(state: DiagnosticState) {
    await handleCompleteDiagnosticTest(state, this.createDiagnosticHandlersProps());
  }
  
  // Handle courses list
  async handleCoursesList() {
    await handleCoursesList(this.createCourseHandlersProps());
  }
  
  // Handle start course
  async handleStartCourse(courseId: string) {
    await handleStartCourse(courseId, this.createCourseHandlersProps());
  }
  
  // Handle navigate course page
  async handleNavigateCoursePage(courseId: string, pageIndex: number) {
    await handleNavigateCoursePage(courseId, pageIndex, this.createCourseHandlersProps());
  }
  
  // Handle complete course
  async handleCompleteCourse(courseId: string) {
    await handleCompleteCourse(courseId, this.createCourseHandlersProps());
  }
  
  // Handle submit course quiz
  async handleSubmitCourseQuiz(courseId: string, pageIndex: number, selectedOption: string, correct: boolean, currentTotalPages?: number) {
    await handleSubmitCourseQuiz(courseId, pageIndex, selectedOption, correct, this.createCourseHandlersProps(), currentTotalPages);
  }
  
  // Handle quiz answer
  async handleQuizAnswer(selectedOption: number, correct: boolean, currentQuiz: QuizQuestion | null) {
    await handleQuizAnswer(selectedOption, correct, currentQuiz, this.createQuizHandlersProps());
  }
  
  // Handle file upload
  async handleFileUpload(files: FileList) {
    await handleFileUpload(files, this.createFileHandlersProps());
  }
  
  // Handle remove file
  async handleRemoveFile(fileIndex: number) {
    await handleRemoveFile(fileIndex, this.createFileHandlersProps());
  }
  
  // Course quiz answer selection
  handleCourseQuizAnswerSelection(questionIndex: number, selectedOption: number, courseQuizAnswers: CourseQuizAnswers) {
    const newAnswers = handleCourseQuizAnswer(courseQuizAnswers, questionIndex, selectedOption);
    this.setCourseQuizAnswers(newAnswers);
  }
  
  // Course quiz navigation
  handleCourseQuizNavigation(direction: 'next' | 'previous' | number, courseQuiz: CourseQuizState | null, courseQuizAnswers: CourseQuizAnswers) {
    if (!courseQuiz) return;
    
    let newAnswers = courseQuizAnswers;
    
    if (direction === 'next') {
      newAnswers = navigateToNextQuizQuestion(courseQuizAnswers, courseQuiz.questions.length);
    } else if (direction === 'previous') {
      newAnswers = navigateToPreviousQuizQuestion(courseQuizAnswers);
    } else if (typeof direction === 'number') {
      newAnswers = navigateToQuizQuestion(courseQuizAnswers, direction, courseQuiz.questions.length);
    }
    
    this.setCourseQuizAnswers(newAnswers);
  }
}

interface ChatWidgetProps {
  apiUrl?: string;
  position?: 'bottom-right' | 'bottom-left' | 'fullscreen';
  theme?: 'light' | 'dark';
}

export const ChatWidget: React.FC<ChatWidgetProps> = ({
  apiUrl = 'https://backend-647308514289.us-central1.run.app',
  // apiUrl = 'http://localhost:8080',
  position = 'fullscreen',
  theme = 'light'
}) => {
  // Authentication State
  const [isAuthenticated, setIsAuthenticated] = useState(!!Cookies.get('auth_token') && !!Cookies.get('refresh_token') && !!localStorage.getItem('moneymentor_user_id'));
  const [showSessionExpiredModal, setShowSessionExpiredModal] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [recentLoginTime, setRecentLoginTime] = useState<number | null>(null);
  // Add a ref to track the timeout
  const sessionModalTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (showSessionExpiredModal) {
      // Set a timeout to auto-logout after 60 seconds (appropriate for 60-minute sessions)
      sessionModalTimeoutRef.current = setTimeout(() => {
        handleLogout();
      }, 60 * 1000);
    } else {
      // Clear the timeout if modal is closed
      if (sessionModalTimeoutRef.current) {
        clearTimeout(sessionModalTimeoutRef.current);
        sessionModalTimeoutRef.current = null;
      }
    }
    // Cleanup on unmount
    return () => {
      if (sessionModalTimeoutRef.current) {
        clearTimeout(sessionModalTimeoutRef.current);
        sessionModalTimeoutRef.current = null;
      }
    };
  }, [showSessionExpiredModal]);
  
  // Add a ref to store the interval ID
  const authIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  useEffect(() => {
    const checkAuth = () => {
      const token = Cookies.get('auth_token');
      const refreshToken = Cookies.get('refresh_token');
      const userId = localStorage.getItem('moneymentor_user_id');
      
      const isNowAuthenticated = !!(token && refreshToken && userId);
      const wasAuthenticated = isAuthenticated;
      
      if (isNowAuthenticated !== wasAuthenticated) {
        if (isNowAuthenticated) {
          console.log('🔐 User authenticated:', { token: !!token, refreshToken: !!refreshToken, userId: !!userId });
        } else {
          console.log('🚪 User logged out or session expired');
        }
      }
      
      // Debug logging for session issues
      if (isNowAuthenticated && !wasAuthenticated) {
        console.log('🔐 User just logged in:', { token: !!token, refreshToken: !!refreshToken, userId: !!userId });
      }
      
      // Check if session is about to expire (within 5 minutes for 60-minute sessions)
      if (isNowAuthenticated) {
        const sessionInfo = getSessionInfo();
        if (sessionInfo) {
          // Only log session info every 5 minutes to reduce console spam
          const now = Date.now();
          const lastLogTime = sessionInfo.lastLogTime || 0;
          if (now - lastLogTime > 5 * 60 * 1000) { // 5 minutes
            console.log('⏰ Session info:', {
              expiresAt: sessionInfo.expiresAt,
              timeUntilExpiry: Math.round(sessionInfo.timeUntilExpiry / 1000 / 60), // minutes
              isExpired: sessionInfo.isExpired
            });
            // Update last log time
            sessionInfo.lastLogTime = now;
          }
          
          // Only show expiration warning if we have valid expiration data
          if (sessionInfo.expiresAt && sessionInfo.timeUntilExpiry > 0 && sessionInfo.timeUntilExpiry <= 5 * 60 * 1000) {
            console.log('⚠️ Session will expire within 5 minutes');
            setShowSessionExpiredModal(true);
          }
        } else {
          console.log('⚠️ No session info available - auth_token_expires may not be set');
        }
      }
      
      setIsAuthenticated(isNowAuthenticated);
    };
    
    // Clear any existing interval
    if (authIntervalRef.current) {
      clearInterval(authIntervalRef.current);
      authIntervalRef.current = null;
    }
    
    // Add a small delay to prevent immediate session check after login
    const initialDelay = setTimeout(() => {
      checkAuth();
      // Set up interval and store the ID
      authIntervalRef.current = setInterval(checkAuth, 30000); // Check every 30 seconds instead of every second
    }, 1000); // 1 second delay
    
    return () => {
      clearTimeout(initialDelay);
      if (authIntervalRef.current) {
        clearInterval(authIntervalRef.current);
        authIntervalRef.current = null;
      }
    };
  }, [isAuthenticated]);
  
  const handleAuthSuccess = (userData?: any) => {
    setIsAuthenticated(true);
    setRecentLoginTime(Date.now()); // Track when user logged in
    
    // Update user profile with data from login response
    if (userData?.user) {
      const { first_name, last_name, email } = userData.user;
      const fullName = `${first_name} ${last_name}`.trim();
      
      profileHook.updateProfile({
        name: fullName,
        email: email,
        joinDate: new Date().toISOString(), // Will be updated when profile is fetched
      });
    }
  };
  
  const handleSessionExpiredStayLoggedIn = () => {
    setShowSessionExpiredModal(false);
    setIsAuthenticated(true);
  };
  
  const handleSessionExpiredLogout = () => {
    setShowSessionExpiredModal(false);
    setIsAuthenticated(false);
  };

  const handleLogout = async () => {
    if (isLoggingOut) return; // Prevent multiple clicks
    
    setIsLoggingOut(true);
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
      setIsLoggingOut(false);
    }
  };

  // --- All other hooks below ---
  const [isOpen, setIsOpen] = useState(false);
  const [activeMode, setActiveMode] = useState('chat');
  const { sessionIds, setSessionIds } = useSessionState();
  const sidebarHook = useSidebar();
  const profileHook = useProfile();
  const currentTheme = profileHook.userProfile.preferences.theme;
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [sessionsError, setSessionsError] = useState<string | null>(null);
  const [chatMessageCount, setChatMessageCount] = useState(0);
  const [chatQuizTotalAnswered, setChatQuizTotalAnswered] = useState(0);
  const [chatQuizCorrectAnswered, setChatQuizCorrectAnswered] = useState(0);
  const [showQuizDropdown, setShowQuizDropdown] = useState(false);
  const [chatQuizHistory, setChatQuizHistory] = useState<any[]>([]);
  const [currentWindow, setCurrentWindow] = useState<'intro' | 'chat' | 'learn'>('intro');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [learnMessages, setLearnMessages] = useState<ChatMessage[]>([]);
  const [chatInputValue, setChatInputValue] = useState('');
  const [learnInputValue, setLearnInputValue] = useState('');
  const [chatIsLoading, setChatIsLoading] = useState(false);
  const [learnIsLoading, setLearnIsLoading] = useState(false);
  const [chatCurrentQuiz, setChatCurrentQuiz] = useState<QuizQuestion | null>(null);
  const [chatShowQuizFeedback, setChatShowQuizFeedback] = useState(false);
  const [chatLastQuizAnswer, setChatLastQuizAnswer] = useState<QuizFeedback | null>(null);
  const [chatDiagnosticState, setChatDiagnosticState] = useState<DiagnosticState>(initializeDiagnosticState());
  const [chatIsDiagnosticMode, setChatIsDiagnosticMode] = useState(false);
  const [chatShowDiagnosticFeedback, setChatShowDiagnosticFeedback] = useState(false);
  const [chatDiagnosticFeedback, setChatDiagnosticFeedback] = useState<QuizFeedback | null>(null);
  const [chatAvailableCourses, setChatAvailableCourses] = useState<Course[]>([]);
  const [chatCurrentCourse, setChatCurrentCourse] = useState<Course | null>(null);
  const [chatCurrentCoursePage, setChatCurrentCoursePage] = useState<CoursePage | null>(null);
  const [chatShowCourseList, setChatShowCourseList] = useState(false);
  const [chatCourseQuiz, setChatCourseQuiz] = useState<CourseQuizState | null>(null);
  const [chatCourseQuizAnswers, setChatCourseQuizAnswers] = useState<CourseQuizAnswers>(initializeCourseQuizAnswers(0));
  const [learnCurrentQuiz, setLearnCurrentQuiz] = useState<QuizQuestion | null>(null);
  const [learnShowQuizFeedback, setLearnShowQuizFeedback] = useState(false);
  const [learnLastQuizAnswer, setLearnLastQuizAnswer] = useState<QuizFeedback | null>(null);
  const [learnDiagnosticState, setLearnDiagnosticState] = useState<DiagnosticState>(initializeDiagnosticState());
  const [learnIsDiagnosticMode, setLearnIsDiagnosticMode] = useState(false);
  const [learnShowDiagnosticFeedback, setLearnShowDiagnosticFeedback] = useState(false);
  const [learnDiagnosticFeedback, setLearnDiagnosticFeedback] = useState<QuizFeedback | null>(null);
  const [learnCurrentDiagnosticQuestionIndex, setLearnCurrentDiagnosticQuestionIndex] = useState(0);
  const [learnDiagnosticTotalQuestions, setLearnDiagnosticTotalQuestions] = useState(0);
  const [learnAvailableCourses, setLearnAvailableCourses] = useState<Course[]>([]);
  const [learnCurrentCourse, setLearnCurrentCourse] = useState<Course | null>(null);
  const [learnCurrentCoursePage, setLearnCurrentCoursePage] = useState<CoursePage | null>(null);
  const [learnShowCourseList, setLearnShowCourseList] = useState(false);
  const [learnCourseQuiz, setLearnCourseQuiz] = useState<CourseQuizState | null>(null);
  const [learnCourseQuizAnswers, setLearnCourseQuizAnswers] = useState<CourseQuizAnswers>(initializeCourseQuizAnswers(0));
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>(initializeUploadProgress());
  const messagesEndRef = useScrollToBottom([chatMessages, learnMessages, currentWindow]);
  
  // Loading states for specific API calls
  const [chatQuizGenerating, setChatQuizGenerating] = useState(false);
  const [learnQuizGenerating, setLearnQuizGenerating] = useState(false);
  const [chatQuizSubmitting, setChatQuizSubmitting] = useState(false);
  const [learnQuizSubmitting, setLearnQuizSubmitting] = useState(false);
  const [chatCourseGenerating, setChatCourseGenerating] = useState(false);
  const [learnCourseGenerating, setLearnCourseGenerating] = useState(false);
  const [chatCourseCompleting, setChatCourseCompleting] = useState(false);
  const [learnCourseCompleting, setLearnCourseCompleting] = useState(false);
  const [chatDiagnosticGenerating, setChatDiagnosticGenerating] = useState(false);
  const [learnDiagnosticGenerating, setLearnDiagnosticGenerating] = useState(false);
  const [learnCourseGenerationLoading, setLearnCourseGenerationLoading] = useState(false);
  
  // Learning Center Page Navigation State
  const [learnCurrentPage, setLearnCurrentPage] = useState<LearningPage>('courses');
  const [learnSelectedCourseKey, setLearnSelectedCourseKey] = useState<string>('');
  const [learnSelectedCourseLabel, setLearnSelectedCourseLabel] = useState<string>('');

  // Get user ID from backend (stored during login)
  const userId = localStorage.getItem('moneymentor_user_id');
  
  // Only set session ID if user is authenticated
  let currentSessionId = '';
  if (isAuthenticated && sessionIds.sessionId) {
    currentSessionId = sessionIds.sessionId;
  } else if (isAuthenticated) {
    // User is authenticated but no session ID, create one
    setNewChatSession();
    currentSessionId = localStorage.getItem('moneymentor_session_id') || uuidv4();
    setSessionIds({ ...sessionIds, sessionId: currentSessionId });
  }
  
  const [apiConfig, setApiConfig] = useState<ApiConfig>({
    apiUrl,
    userId: userId || '',
    sessionId: currentSessionId
  });
  
  // Update apiConfig when session ID changes (only if authenticated)
  useEffect(() => {
    if (isAuthenticated) {
      setApiConfig({
        apiUrl,
        userId: userId || '',
        sessionId: sessionIds.sessionId || currentSessionId
      });
    } else {
      // Clear sessionId when not authenticated
      setApiConfig({
        apiUrl,
        userId: '',
        sessionId: ''
      });
    }
  }, [sessionIds.sessionId, userId, apiUrl, isAuthenticated]);

  // Session management functions
  const handleSessionSelect = async (sessionId: string) => {
    try {
      // Set the active session
      setActiveSession(sessionId);
      setSessionIds({ ...sessionIds, sessionId });
      
      // Clear current chat messages
      setChatMessages([]);
      // Clear quiz state and generation
      setChatCurrentQuiz(null);
      setChatQuizGenerating(false);
      setChatShowQuizFeedback(false);
      setChatLastQuizAnswer(null);
      
      // Fetch session history from backend
      const sessionHistory = await getSessionHistory(apiConfig, sessionId);
      
      // Transform backend messages to ChatMessage format
      const transformedMessages: ChatMessage[] = sessionHistory.chat_history?.map((msg: any) => ({
        id: msg.id || `msg_${Date.now()}_${Math.random()}`,
        content: msg.content,
        type: msg.role === 'user' ? 'user' : 'assistant',
        timestamp: msg.timestamp || new Date().toISOString(),
        sessionId: sessionId,
        userId: userId || '',
        metadata: msg.metadata || {}
      })) || [];
      
      setChatMessages(transformedMessages);
      
      // Update sidebar state
      sidebarHook.setSidebarState({
        ...sidebarHook.sidebarState,
        selectedSessionId: sessionId
      });
      
    } catch (error) {
      console.error('Failed to load session:', error);
      // Show error message to user
      setChatMessages([{
        id: `error_${Date.now()}`,
        content: 'Failed to load chat history. Please try again.',
        type: 'system',
        timestamp: new Date().toISOString(),
        sessionId: sessionId,
        userId: userId || ''
      }]);
    }
  };

  const handleNewChat = () => {
    // Clear current session and generate new UUID
    setNewChatSession();
    const newSessionId = localStorage.getItem('moneymentor_session_id') || uuidv4();
    setSessionIds({ ...sessionIds, sessionId: newSessionId });
    
    // Clear chat messages
    setChatMessages([]);
    
    // Clear sidebar selection
    sidebarHook.setSidebarState({
      ...sidebarHook.sidebarState,
      selectedSessionId: null
    });
    
    // Close sidebar on mobile
    if (window.innerWidth <= 768) {
      sidebarHook.setSidebarState({
        ...sidebarHook.sidebarState,
        isOpen: false
      });
    }
  };

  // Handle session deletion
  const handleSessionDelete = async (sessionId: string) => {
    try {
      // Call the delete session API
      await deleteSession(apiConfig, sessionId);
      
      // Remove the session from the local state
      setChatSessions(prev => prev.filter(session => session.id !== sessionId));
      
      // If the deleted session was the currently selected one, clear the selection
      if (sidebarHook.sidebarState.selectedSessionId === sessionId) {
        sidebarHook.setSidebarState({
          ...sidebarHook.sidebarState,
          selectedSessionId: null
        });
        
        // Clear chat messages if the deleted session was active
        setChatMessages([]);
      }
      
      // Show success message
      console.log('Session deleted successfully');
      
    } catch (error) {
      console.error('Failed to delete session:', error);
      throw error; // Re-throw to let the UI handle the error
    }
  };

  // Fetch sessions from backend
  const fetchSessions = async () => {
    if (!apiConfig || !userId) return;
    
    setIsLoadingSessions(true);
    setSessionsError(null);
    
    try {
      const response = await getAllUserSessions(apiConfig);
      
      // Handle backend response format: { sessions: { sessionId: [messages] } }
      let sessionsArr: any[] = [];
      
      if (response && response.sessions) {
        // Convert object format to array format
        sessionsArr = Object.entries(response.sessions).map(([sessionId, messages]: [string, any]) => {
          const messageArray = Array.isArray(messages) ? messages : [];
          // Find first user and first assistant message
          const firstUserMsg = messageArray.find((m: any) => m.user);
          const firstAssistantMsg = messageArray.find((m: any) => m.assistant);
          return {
            session_id: sessionId,
            title: firstUserMsg ? firstUserMsg.user.slice(0, 40) : `Chat ${sessionId.slice(-6)}`,
            preview: firstAssistantMsg ? firstAssistantMsg.assistant.slice(0, 60) : 'No preview available',
            timestamp: new Date().toISOString(), // Use current time as fallback
            message_count: messageArray.length,
            last_activity: new Date().toISOString(),
            chat_history: messageArray,
            tags: []
          };
        });
      } else if (Array.isArray(response)) {
        sessionsArr = response;
      } else if (Array.isArray(response.sessions)) {
        sessionsArr = response.sessions;
      }
      
      // Transform backend response to ChatSession format
      const transformedSessions: ChatSession[] = sessionsArr.map((session: any) => ({
        id: session.session_id,
        title: session.title || `Chat ${session.session_id?.slice(-6) || ''}`,
        preview: session.preview || (session.chat_history && session.chat_history.length > 0 ? 
          (session.chat_history[0].user || session.chat_history[0].assistant || 'No preview available') : 'No preview available'),
        timestamp: session.timestamp || session.lastActivity || new Date().toISOString(),
        messageCount: session.message_count || (session.chat_history ? session.chat_history.length : 0),
        lastActivity: session.last_activity || session.timestamp || new Date().toISOString(),
        tags: session.tags || [],
        isActive: session.session_id === localStorage.getItem('moneymentor_session_id')
      }));
      
      setChatSessions(transformedSessions);
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
      setSessionsError(error instanceof Error ? error.message : 'Failed to load sessions');
    } finally {
      setIsLoadingSessions(false);
    }
  };

  // Fetch sessions when sidebar opens
  useEffect(() => {
    if (sidebarHook.sidebarState.isOpen && userId) {
      fetchSessions();
    }
  }, [sidebarHook.sidebarState.isOpen, userId]);

  // Create window instances
  const chatWindow = new WindowInstance(
    apiConfig,
    sessionIds,
    'chat',
    (message) => setChatMessages(prev => [...prev, message]),
    setChatInputValue,
    setChatIsLoading,
    setChatCurrentQuiz,
    setChatShowQuizFeedback,
    setChatLastQuizAnswer,
    setChatDiagnosticState,
    setChatIsDiagnosticMode,
    setChatShowDiagnosticFeedback,
    setChatDiagnosticFeedback,
    setChatAvailableCourses,
    setChatShowCourseList,
    setChatCurrentCoursePage,
    setChatCurrentCourse,
    setChatCourseQuiz,
    setChatCourseQuizAnswers,
    setUploadedFiles,
    setUploadProgress,
    (pattern) => setChatMessages(prev => prev.filter(msg => !msg.content.includes(pattern))),
    setChatQuizGenerating,
    setChatCourseGenerating,
    setChatCourseCompleting,
    setChatQuizSubmitting
  );

  const learnWindow = new WindowInstance(
    apiConfig,
    sessionIds,
    'learn',
    (message) => setLearnMessages(prev => [...prev, message]),
    setLearnInputValue,
    setLearnIsLoading,
    setLearnCurrentQuiz,
    setLearnShowQuizFeedback,
    setLearnLastQuizAnswer,
    setLearnDiagnosticState,
    setLearnIsDiagnosticMode,
    setLearnShowDiagnosticFeedback,
    setLearnDiagnosticFeedback,
    setLearnAvailableCourses,
    setLearnShowCourseList,
    setLearnCurrentCoursePage,
    setLearnCurrentCourse,
    setLearnCourseQuiz,
    setLearnCourseQuizAnswers,
    () => {}, // No file upload for learn window
    () => {}, // No upload progress for learn window
    (pattern) => setLearnMessages(prev => prev.filter(msg => !msg.content.includes(pattern))),
    setLearnDiagnosticGenerating,
    setLearnCourseGenerating,
    setLearnCourseCompleting,
    setLearnQuizSubmitting
  );

  // Initialize session when widget opens
  useEffect(() => {
    if (isOpen && sessionIds.userId) {
      // Ensure session ID is available
      if (!sessionIds.sessionId) {
        setNewChatSession();
        const newSessionId = localStorage.getItem('moneymentor_session_id') || uuidv4();
        setSessionIds({ ...sessionIds, sessionId: newSessionId });
      }
      
      // If this is the first time opening and no messages exist, treat it like a new chat
      if (chatMessages.length === 0 && learnMessages.length === 0) {
        handleNewChat();
      } else {
      handleInitializeSession();
    }
    }
  }, [isOpen, sessionIds.userId]);

  // Session initialization
  const handleInitializeSession = async () => {
    try {
      // Initialize both windows with welcome messages
      chatWindow.initializeWelcome();
      learnWindow.initializeWelcome();
    } catch (error) {
      console.error('Session initialization error:', error);
      chatWindow.initializeWelcome();
      learnWindow.initializeWelcome();
    }
  };

  // Window-specific input change handlers
  const handleChatInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setChatInputValue(value);
    
    // Chat window doesn't process commands - just update input value
  };

  // Window-specific message handlers
  const handleChatSendMessage = async (commandText?: string) => {
    const messageText = commandText || chatInputValue.trim();
    if (!messageText) return;
    
    // For chat window, always send to chat API and increment counter
    setChatIsLoading(true);
    setChatInputValue('');
    
    try {
      // Add user message to chat
      const userMessage = createUserMessage(
        messageText,
        apiConfig.sessionId,
        sessionIds.userId
      );
      setChatMessages(prev => [...prev, userMessage]);

      // Increment message counter
      const newMessageCount = chatMessageCount + 1;
      setChatMessageCount(newMessageCount);

      // Send to chat API using streaming
      let fullResponse: any = null;
      let streamingContent = '';
      let assistantMessageId = '';

      // Create initial assistant message with "Thinking..." state
      const initialAssistantMessage = createAssistantMessage(
        '**Thinking...**',
        apiConfig.sessionId,
        sessionIds.userId
      );
      assistantMessageId = initialAssistantMessage.id;
      
      // Add the initial "Thinking..." message
      setChatMessages(prev => [...prev, initialAssistantMessage]);
      
      await sendChatMessageStream(
        apiConfig,
        messageText,
        (chunk: string) => {
          // Update the streaming content
          streamingContent += chunk;
          
          // Update the assistant message with streaming content
          setChatMessages(prev => {
            const newMessages = [...prev];
            const messageIndex = newMessages.findIndex(msg => msg.id === assistantMessageId);
            
            if (messageIndex !== -1) {
              // Remove "Thinking..." and show actual content
              const displayContent = streamingContent.trim() || '**Thinking...**';
              newMessages[messageIndex] = {
                ...newMessages[messageIndex],
                content: displayContent
              };
            }
            
            return newMessages;
          });
        },
        (response: any) => {
          fullResponse = response;
          
          // Update session ID if backend returns a different one
          if (response.session_id && response.session_id !== apiConfig.sessionId) {
            setActiveSession(response.session_id);
            setSessionIds({ ...sessionIds, sessionId: response.session_id });
            
            // Update the session ID in all messages
            setChatMessages(prev => prev.map(msg => ({
              ...msg,
              sessionId: response.session_id
            })));
          }
        },
        (error: Error) => {
          console.error('Streaming error:', error);
          
          // Remove the "Thinking..." message and replace with error
          setChatMessages(prev => {
            const newMessages = prev.filter(msg => msg.id !== assistantMessageId);
          const errorMessage = createSystemMessage(
              error.message || 'An error occurred while processing your request. Please try again.',
              apiConfig.sessionId,
            sessionIds.userId
          );
            return [...newMessages, errorMessage];
          });
        }
      );
      
      if (!fullResponse) {
        throw new Error('No response received');
      }
      
      const response = fullResponse;
      
      // Handle backend response - only process metadata and quiz, don't create duplicate message
      if (response.message) {
        // Check if message contains calculation JSON
        const jsonMatch = response.message.match(/```json\n([\s\S]*?)\n```/);
        let calculationResult: any = null;
        
        if (jsonMatch) {
          try {
            const jsonData = JSON.parse(jsonMatch[1]);
            // Convert snake_case to camelCase for the component
            calculationResult = {
              type: jsonData.type || 'financial_calculation',
              monthlyPayment: jsonData.monthly_payment,
              monthsToPayoff: jsonData.months_to_payoff,
              totalInterest: jsonData.total_interest,
              totalAmount: jsonData.total_amount,
              stepByStepPlan: jsonData.step_by_step_plan || [],
              disclaimer: "Estimates only. Verify with a certified financial professional.",
              metadata: {
                inputValues: {},
                calculationDate: new Date().toISOString()
              }
            };
            
            // Update the last message (the streaming message) with calculation metadata
            if (calculationResult) {
              setChatMessages(prev => {
                const newMessages = [...prev];
                const messageIndex = newMessages.findIndex(msg => msg.id === assistantMessageId);
                
                if (messageIndex !== -1) {
                  newMessages[messageIndex] = {
                    ...newMessages[messageIndex],
                    metadata: {
                      ...newMessages[messageIndex].metadata,
                      calculationResult
                    }
                    };
                  }
                
                return newMessages;
              });
            }
          } catch (parseError) {
            console.error('Failed to parse calculation JSON:', parseError);
          }
        }
        
        // Handle quiz questions
        if (response.quiz) {
          setChatCurrentQuiz(response.quiz);
          setChatShowQuizFeedback(false);
        }
      }
      
      // After successful message send, check if we should generate a quiz
      await fetchChatCountAndMaybeTriggerQuiz(apiConfig.sessionId);
      
    } catch (error) {
      console.error('Chat message error:', error);
      const errorMessage = createSystemMessage(
        'Failed to send message. Please try again.',
        apiConfig.sessionId,
        sessionIds.userId
      );
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setChatIsLoading(false);
    }
  };

  // Window-specific wrapper functions for components
  
  const handleChatDiagnosticQuizAnswer = (selectedOption: number, correct: boolean) => 
    chatWindow.handleDiagnosticQuizAnswer(selectedOption, correct, chatDiagnosticState);

  const handleChatStartCourse = (courseId: string) => chatWindow.handleStartCourse(courseId);
  const handleChatNavigateCoursePage = (pageIndex: number) => chatWindow.handleNavigateCoursePage(chatCurrentCourse?.id || '', pageIndex);
  const handleChatCompleteCourse = () => chatWindow.handleCompleteCourse(chatCurrentCourse?.id || '');
  const handleChatSubmitCourseQuiz = (selectedOption: number, correct: boolean) => {
    const pageIndex = chatCourseQuiz?.pageIndex ?? 0;
    const selectedOptionLetter = String.fromCharCode(65 + selectedOption); // Convert 0,1,2,3 to A,B,C,D
    const currentTotalPages = chatCourseQuiz?.totalPages; // Get current total pages from quiz state
    return chatWindow.handleSubmitCourseQuiz(chatCurrentCourse?.id || '', pageIndex, selectedOptionLetter, correct, currentTotalPages);
  };
  const handleChatQuizAnswer = async (selectedOption: number, correct: boolean) => {
    // Clear quiz state immediately to hide the container
    setChatCurrentQuiz(null);
    setChatShowQuizFeedback(false);
    setChatLastQuizAnswer(null);
    
    // Increment total answered
    setChatQuizTotalAnswered(prev => prev + 1);
    // Increment correct answered if correct
    if (correct) setChatQuizCorrectAnswered(prev => prev + 1);

    // Build feedback string
    const feedbackTitle = correct ? '🎉 Excellent! You got it right!' : '🤔 Good Try! Here\'s what you should know:';
    const feedbackExplanation = chatCurrentQuiz?.explanation || '';
    const feedbackContent = `${feedbackTitle}\n\n💡 ${feedbackExplanation}`;

    // Add feedback as a normal assistant message
    setChatMessages(prev => [
      ...prev,
      createAssistantMessage(
        feedbackContent,
            sessionIds.sessionId,
            sessionIds.userId
      )
    ]);

    // Add to quiz history
    if (chatCurrentQuiz) {
      setChatQuizHistory(prev => [
        ...prev,
        {
          question: chatCurrentQuiz.question,
          options: chatCurrentQuiz.options,
          correctAnswer: chatCurrentQuiz.correctAnswer,
          userAnswer: selectedOption,
          explanation: chatCurrentQuiz.explanation,
          topicTag: chatCurrentQuiz.topicTag || '',
        }
      ]);
      
      // Submit micro quiz answer to backend
      try {
        await submitMicroQuiz(apiConfig, chatCurrentQuiz.id || '', chatCurrentQuiz, selectedOption, correct, sessionIds.userId);
      } catch (err) {
        console.error('Failed to submit micro quiz:', err);
      }
    }
  };
  const handleChatFileUpload = async (files: FileList) => {
    const validation = validateFiles(files);
    
    if (validation.validFiles.length === 0) {
      const errorMessage = createSystemMessage(
        'Please upload valid files (PDF, TXT, PPT, PPTX) under 10MB each.',
        sessionIds.sessionId,
        sessionIds.userId
      );
      setChatMessages(prev => [...prev, errorMessage]);
      return;
    }

    setUploadProgress({ isUploading: true, progress: 0 });

    try {
      for (let i = 0; i < validation.validFiles.length; i++) {
        const file = validation.validFiles[i];
        
        try {
          await uploadFile(apiConfig, file);
          setUploadedFiles(prev => [...prev, file]);
          
          const successMessage = createSystemMessage(
            `File "${file.name}" uploaded successfully!`,
            sessionIds.sessionId,
            sessionIds.userId
          );
          setChatMessages(prev => [...prev, successMessage]);
        } catch (error) {
          const errorMessage = createSystemMessage(
            `Failed to upload "${file.name}": ${error instanceof Error ? error.message : 'Unknown error'}`,
            sessionIds.sessionId,
            sessionIds.userId
          );
          setChatMessages(prev => [...prev, errorMessage]);
        }

        setUploadProgress(updateUploadProgress(i + 1, validation.validFiles.length, file.name));
      }
    } catch (error) {
      console.error('Upload error:', error);
      const errorMessage = createSystemMessage(
        'Upload failed. Please check your connection and try again.',
        sessionIds.sessionId,
        sessionIds.userId
      );
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setUploadProgress(resetUploadProgress());
    }
  };
  const handleChatRemoveFile = async (fileIndex: number) => {
    // Safety check before attempting to remove
    if (fileIndex < 0 || fileIndex >= uploadedFiles.length) {
      console.error('Invalid file index:', fileIndex, 'uploadedFiles length:', uploadedFiles.length);
      return;
    }

    const file = uploadedFiles[fileIndex];
    if (!file) {
      console.error('File not found at index:', fileIndex);
      return;
    }

    try {
      // Remove file from local state immediately
      const updatedFiles = uploadedFiles.filter((_, index) => index !== fileIndex);
      setUploadedFiles(updatedFiles);
      
      // Add removal message
      const removalMessage = createSystemMessage(
        `File "${file.name}" has been removed.`,
        sessionIds.sessionId,
        sessionIds.userId
      );
      setChatMessages(prev => [...prev, removalMessage]);
      
      // Optionally try to remove from backend, but don't fail if it doesn't work
      try {
        // await removeFile(apiConfig, file.name);
        // Backend remove endpoint might not exist, so we'll just remove locally
      } catch (backendError) {
        console.warn('Backend file removal failed, but file removed locally:', backendError);
      }
    } catch (error) {
      console.error('Remove file error:', error);
      const errorMessage = createSystemMessage(
        'Failed to remove file. Please try again.',
        sessionIds.sessionId,
        sessionIds.userId
      );
      setChatMessages(prev => [...prev, errorMessage]);
    }
  };
  const handleChatCourseQuizAnswerSelection = (questionIndex: number, selectedOption: number) => 
    chatWindow.handleCourseQuizAnswerSelection(questionIndex, selectedOption, chatCourseQuizAnswers);
  const handleChatCourseQuizNavigation = (direction: 'next' | 'previous' | number) => {
    if (direction === 'previous' && chatCourseQuiz) {
      // Navigate to previous page
      const prevPageIndex = chatCourseQuiz.pageIndex - 1;
      if (prevPageIndex >= 0) {
        handleChatNavigateCoursePage(prevPageIndex);
      }
    } else if (direction === 'next' && chatCourseQuiz) {
      // Navigate to next page
      const nextPageIndex = chatCourseQuiz.pageIndex + 1;
      handleChatNavigateCoursePage(nextPageIndex);
    } else {
      // Original quiz navigation logic for question-level navigation
    chatWindow.handleCourseQuizNavigation(direction, chatCourseQuiz, chatCourseQuizAnswers);
    }
  };

 
  const handleLearnDiagnosticQuizAnswer = (selectedOption: number, correct: boolean) => 
    learnWindow.handleDiagnosticQuizAnswer(selectedOption, correct, learnDiagnosticState);
  
  // Custom diagnostic completion handler for learn window
  const handleLearnCompleteDiagnosticTest = async (state: DiagnosticState) => {
    console.log('🎯 Starting diagnostic test completion process:', {
      quizId: state.quizId,
      questionsCount: state.test?.questions.length,
      answersCount: state.answers.length,
      userId: sessionIds.userId,
      hasBackendResult: !!state.backendResult,
      selectedCourseType: state.selectedCourseType
    });
    
    console.log('🔍 Current learnDiagnosticState:', {
      currentQuestionIndex: learnDiagnosticState.currentQuestionIndex,
      totalQuestions: learnDiagnosticState.test?.questions.length,
      isActive: learnDiagnosticState.isActive,
      hasTest: !!learnDiagnosticState.test
    });

    try {
      // Show course generation loading state
      console.log('🚀 Setting course generation loading state...');
      setLearnCourseGenerationLoading(true);
      setLearnCurrentPage('course-generation');
      console.log('✅ Course generation page set, loading state active');
      
      let result;
      
      // Check if we already have a backend result from the redirect
      if (state.backendResult) {
        console.log('🔄 Using backend result from redirect:', state.backendResult);
        result = state.backendResult;
      } else {
        // Submit diagnostic quiz (fallback for direct calls)
        console.log('📤 Submitting diagnostic quiz to backend...');
        console.log('📋 Quiz data being sent:', {
          quizId: state.quizId,
          questions: state.test?.questions,
          answers: state.answers,
          userId: sessionIds.userId,
          selectedCourseType: state.selectedCourseType
        });
        
        console.log('🔍 CALLING submitDiagnosticQuizAnswers with:');
        console.log('  📋 apiConfig:', apiConfig);
        console.log('  🆔 state.quizId:', state.quizId);
        console.log('  📝 state.test!.questions:', state.test!.questions);
        console.log('  📊 state.answers:', state.answers);
        console.log('  👤 sessionIds.userId:', sessionIds.userId);
        console.log('  🎯 selectedCourseType:', state.selectedCourseType);
        console.log('🔍 Full diagnostic state:', state);
        
        result = await submitDiagnosticQuizAnswers(
          apiConfig,
          state.quizId!,
          state.test!.questions,
          state.answers,
          sessionIds.userId,
          state.selectedCourseType
        );
      }
      
      console.log('📥 Diagnostic quiz submission result:', result);
      
      if (result) {
        // Check for AI-generated course data
        if (result.ai_generated_course) {
          console.log('✅ AI-generated course received:', result.ai_generated_course);
          
          // Create a course object from AI-generated data
          const aiCourse = {
            id: result.ai_generated_course.course_id,
            title: result.ai_generated_course.title,
            description: `AI-generated course on ${result.ai_generated_course.focus_topic}`,
            difficulty: result.ai_generated_course.course_level,
            topicTag: result.ai_generated_course.focus_topic,
            estimatedTime: '10-15 minutes',
            pages: result.ai_generated_course.pages.map((page: any, index: number) => ({
              id: `ai-page-${index}`,
              title: page.title,
              content: page.content,
              pageNumber: index + 1,
              totalPages: result.ai_generated_course.pages.length, // Use actual number of pages generated
              pageType: 'content'
            })),
            quizQuestions: []
          };
          
          // Set the AI-generated course directly
          setLearnCurrentCourse(aiCourse);
          setLearnCurrentCoursePage(aiCourse.pages[0]);
          
          // Transition to course content
          setLearnCourseGenerationLoading(false);
          setLearnCurrentPage('course-content');
          
          console.log('✅ AI-generated course loaded successfully');
        } else if (result.recommended_course_id) {
          console.log('✅ Course recommended:', result.recommended_course_id);
          
          // Keep the loading state while starting the course
          console.log('🚀 Starting recommended course...');
          
          try {
            // Start the recommended course
            await learnWindow.handleStartCourse(result.recommended_course_id);
            console.log('✅ Course started successfully');
            
            // Now transition to course content
            setLearnCourseGenerationLoading(false);
            setLearnCurrentPage('course-content');
          } catch (courseStartError) {
            console.error('❌ Failed to start course:', courseStartError);
            // Even if course start fails, stay in course generation state
            // Don't go back to course selection
            setLearnCourseGenerationLoading(false);
            // Show error message but stay in current state
            console.log('⚠️ Course start failed, staying in current state');
          }
        } else {
          console.log('ℹ️ No course recommended, but staying in course generation state');
          // Don't go back to courses - stay in course generation state
          // This allows the user to see what happened
          setLearnCourseGenerationLoading(false);
          // Keep the course generation page visible
        }
      } else {
        console.log('⚠️ No result received from backend, staying in course generation state');
        setLearnCourseGenerationLoading(false);
        // Don't go back to courses - stay in current state
        // This allows debugging of what went wrong
      }
    } catch (error) {
      console.error('❌ Failed to complete diagnostic test:', error);
      setLearnCourseGenerationLoading(false);
      // On error, don't go back to courses - stay in current state
      // This allows the user to see the error and retry
      console.log('⚠️ Error occurred, staying in current state for debugging');
    }
  };

  // Handle going back to courses from diagnostic or course content
  const handleLearnBackToCourses = () => {
    // Reset diagnostic state
    setLearnDiagnosticState(initializeDiagnosticState());
    setLearnIsDiagnosticMode(false);
    setLearnShowDiagnosticFeedback(false);
    setLearnDiagnosticFeedback(null);
    
    // Reset course state
    setLearnCurrentCoursePage(null);
    setLearnCurrentCourse(null);
    setLearnCourseQuiz(null);
    setLearnCourseQuizAnswers(initializeCourseQuizAnswers(0));
    
    // Clear selected course
    setLearnSelectedCourseKey('');
    setLearnSelectedCourseLabel('');
    
    // Go back to courses page
    setLearnCurrentPage('courses');
  };
  
  const handleLearnStartCourse = (courseId: string) => learnWindow.handleStartCourse(courseId);
  const handleLearnNavigateCoursePage = (pageIndex: number) => {
    // Check if this is an AI-generated course
    if (learnCurrentCourse && learnCurrentCourse.pages && learnCurrentCourse.pages.length > 0) {
      // For AI-generated courses, navigate directly through the pages array
      if (pageIndex >= 0 && pageIndex < learnCurrentCourse.pages.length) {
        setLearnCurrentCoursePage(learnCurrentCourse.pages[pageIndex]);
        console.log(`📖 Navigated to AI course page ${pageIndex + 1}:`, learnCurrentCourse.pages[pageIndex]);
      } else {
        console.warn(`⚠️ Invalid page index for AI course: ${pageIndex}. Course has ${learnCurrentCourse.pages.length} pages (indices 0-${learnCurrentCourse.pages.length - 1})`);
        // Don't navigate if the page doesn't exist
        return;
      }
    } else {
      // For regular courses, use the existing navigation logic
      learnWindow.handleNavigateCoursePage(learnCurrentCourse?.id || '', pageIndex);
    }
  };
  const handleLearnCompleteCourse = () => {
    // Check if this is an AI-generated course
    if (learnCurrentCourse && learnCurrentCourse.pages && learnCurrentCourse.pages.length > 0) {
      // For AI-generated courses, show completion message and go back to courses
      console.log('🎉 AI-generated course completed!');
      setLearnCurrentCoursePage(null);
      setLearnCurrentCourse(null);
      setLearnCurrentPage('courses');
    } else {
      // For regular courses, use the existing completion logic
      learnWindow.handleCompleteCourse(learnCurrentCourse?.id || '');
    }
  };
  const handleLearnSubmitCourseQuiz = (selectedOption: number, correct: boolean) => {
    const pageIndex = learnCourseQuiz?.pageIndex ?? 0;
    const selectedOptionLetter = String.fromCharCode(65 + selectedOption); // Convert 0,1,2,3 to A,B,C,D
    const currentTotalPages = learnCourseQuiz?.totalPages; // Get current total pages from quiz state
    return learnWindow.handleSubmitCourseQuiz(learnCurrentCourse?.id || '', pageIndex, selectedOptionLetter, correct, currentTotalPages);
  };
  const handleLearnQuizAnswer = (selectedOption: number, correct: boolean) => 
    learnWindow.handleQuizAnswer(selectedOption, correct, learnCurrentQuiz);
  const handleLearnCourseQuizAnswerSelection = (questionIndex: number, selectedOption: number) => 
    learnWindow.handleCourseQuizAnswerSelection(questionIndex, selectedOption, learnCourseQuizAnswers);
  const handleLearnCourseQuizNavigation = (direction: 'next' | 'previous' | number) => {
    if (direction === 'previous' && learnCourseQuiz) {
      // Navigate to previous page
      const prevPageIndex = learnCourseQuiz.pageIndex - 1;
      if (prevPageIndex >= 0) {
        handleLearnNavigateCoursePage(prevPageIndex);
      }
    } else if (direction === 'next' && learnCourseQuiz) {
      // Navigate to next page
      const nextPageIndex = learnCourseQuiz.pageIndex + 1;
      handleLearnNavigateCoursePage(nextPageIndex);
    } else {
      // Original quiz navigation logic for question-level navigation
    learnWindow.handleCourseQuizNavigation(direction, learnCourseQuiz, learnCourseQuizAnswers);
    }
  };

  // Chat window diagnostic variables
  const hasChatDiagnosticTest = chatDiagnosticState.test && chatDiagnosticState.test.questions.length > 0;
  const chatCurrentDiagnosticQuiz = hasChatDiagnosticTest ? chatDiagnosticState.test!.questions[chatDiagnosticState.currentQuestionIndex] : null;
  const chatCurrentDiagnosticQuestionIndex = hasChatDiagnosticTest ? chatDiagnosticState.currentQuestionIndex : 0;
  const chatDiagnosticTotalQuestions = chatDiagnosticState.test ? chatDiagnosticState.test.questions.length : 0;

  // Learn window diagnostic variables - now handled by LearningCenter component

  // Ref for the quiz tracker button
  const quizTrackerRef = React.useRef<HTMLButtonElement>(null);

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

  const [learnHasShownCourseList, setLearnHasShownCourseList] = useState(false);

  // Handler for course selection in Learning Center
  const handleLearnCourseTopicSelect = async (courseKey: string, courseLabel: string) => {
    console.log('🎯 Course selected:', { courseKey, courseLabel });
    
    // Add a message indicating the user selected a course
    setLearnMessages(prev => [
      ...prev,
      {
        id: Date.now().toString(),
        type: 'user',
        content: `Selected course: **${courseLabel}**`,
        timestamp: new Date().toISOString(),
        sessionId: sessionIds.sessionId,
        userId: sessionIds.userId
      }
    ]);
    
    // Fetch diagnostic test for the selected course
    console.log('🚀 Starting diagnostic test for course:', courseKey);
    await learnWindow.handleStartDiagnosticTest(courseKey);
  };

  // Show course list as a persistent chat message on first open of Learning Center
  useEffect(() => {
    if (currentWindow === 'learn' && !learnHasShownCourseList) {
      setLearnMessages(prev => [
        ...prev,
        {
          id: 'learn-courses-list',
          type: 'assistant',
          content: 'Please select a course to get started:',
          timestamp: new Date().toISOString(),
          sessionId: sessionIds.sessionId,
          userId: sessionIds.userId,
          metadata: {
            buttons: LEARN_COURSES.map(course => ({
              label: course.label,
              action: () => handleLearnCourseTopicSelect(course.key, course.label)
            }))
          }
        }
      ]);
      setLearnHasShownCourseList(true);
    }
  }, [currentWindow, learnHasShownCourseList, sessionIds.sessionId, sessionIds.userId]);

  useEffect(() => {
    // Listen for recommended course start event
    const handler = (e: any) => {
      const course = e.detail;
      if (course && course.id) {
        // Start the recommended course using the course ID
        learnWindow.handleStartCourse(course.id);
      }
    };
    window.addEventListener('start-recommended-course', handler);
    return () => window.removeEventListener('start-recommended-course', handler);
  }, [learnWindow]);

  // Add state for loading and error
  const [quizProgressLoading, setQuizProgressLoading] = useState(false);
  const [quizProgressError, setQuizProgressError] = useState<string | null>(null);
  const [quizHistoryLoading, setQuizHistoryLoading] = useState(false);
  const [quizHistoryError, setQuizHistoryError] = useState<string | null>(null);
  const [chatCountLoading, setChatCountLoading] = useState(false);
  const [chatCountError, setChatCountError] = useState<string | null>(null);

  // Fetch quiz progress for the current session
  const fetchQuizProgress = async (sessionId: string) => {
    // Don't fetch quiz progress if user is not authenticated
    if (!isAuthenticated) {
      setChatQuizCorrectAnswered(0);
      setChatQuizTotalAnswered(0);
      return;
    }
    
    setQuizProgressLoading(true);
    setQuizProgressError(null);
    try {
      const progress = await getSessionQuizProgress(apiConfig, sessionId);
      setChatQuizCorrectAnswered(progress.correct_answers);
      setChatQuizTotalAnswered(progress.total_quizzes);
    } catch (err: any) {
      setQuizProgressError(err.message || 'Failed to fetch quiz progress');
      setChatQuizCorrectAnswered(0);
      setChatQuizTotalAnswered(0);
    } finally {
      setQuizProgressLoading(false);
    }
  };

  // Fetch quiz history for the current session
  const fetchQuizHistory = async (sessionId: string) => {
    // Don't fetch quiz history if user is not authenticated
    if (!isAuthenticated) {
      setChatQuizHistory([]);
      return;
    }
    
    setQuizHistoryLoading(true);
    setQuizHistoryError(null);
    try {
      const history = await getSessionQuizHistory(apiConfig, sessionId);
      
      // Transform backend data to match frontend expectations
      const transformedHistory = (history.quiz_history || [])
        .map((quiz: any) => {
          // Only process quizzes that have valid question data
          const questionText = quiz.question_data?.question;
          if (!questionText || questionText.trim() === '') {
            return null; // Skip quizzes without question data
          }
          
          // Handle different formats of choices (array or object)
          let options = ['A', 'B', 'C', 'D'];
          if (quiz.question_data?.choices) {
            if (Array.isArray(quiz.question_data.choices)) {
              options = quiz.question_data.choices;
            } else if (typeof quiz.question_data.choices === 'object') {
              options = Object.values(quiz.question_data.choices);
            }
          }
          
          // Convert correct answer from letter to index
          let correctAnswer = 0;
          if (quiz.question_data?.correct_answer) {
            const correctLetter = quiz.question_data.correct_answer;
            correctAnswer = correctLetter.charCodeAt(0) - 65; // 'A' -> 0, 'B' -> 1, etc.
          }
          
          // Convert user answer from letter to index
          let userAnswer = 0;
          if (quiz.selected) {
            const userLetter = quiz.selected;
            userAnswer = userLetter.charCodeAt(0) - 65; // 'A' -> 0, 'B' -> 1, etc.
          }
          
          return {
            question: questionText,
            options: options,
            correctAnswer: correctAnswer,
            userAnswer: userAnswer,
            explanation: quiz.question_data?.explanation || quiz.explanation || 'No explanation available',
            topicTag: quiz.topic || ''
          };
        })
        .filter((quiz: any) => quiz !== null); // Filter out null entries
      
      setChatQuizHistory(transformedHistory);
    } catch (err: any) {
      setQuizHistoryError(err.message || 'Failed to fetch quiz history');
      setChatQuizHistory([]);
    } finally {
      setQuizHistoryLoading(false);
    }
  };

  // Fetch chat count and trigger quiz if needed
  const fetchChatCountAndMaybeTriggerQuiz = async (sessionId: string) => {
    // Don't fetch chat count if user is not authenticated
    if (!isAuthenticated) {
      setChatMessageCount(0);
      return;
    }
    
    setChatCountLoading(true);
    setChatCountError(null);
    try {
      const countData = await getSessionChatCount(apiConfig, sessionId);
      setChatMessageCount(countData.chat_count);
      if (countData.should_generate_quiz && !chatCurrentQuiz && !chatIsDiagnosticMode) {
        // Show shimmer while generating quiz
        setChatQuizGenerating(true);
        setChatCurrentQuiz(null);
        setChatShowQuizFeedback(false);
        
        // Generate micro quiz
        try {
          const quizData = await generateMicroQuiz(apiConfig);
          // Only set quiz if sessionId is still the active session
          if (sessionIds.sessionId === sessionId) {
            const quizWithId = {
              ...quizData.questions[0],
              id: quizData.quizId // Add the quiz ID to the question object
            };
            setChatCurrentQuiz(quizWithId); // Show first question with ID
            setChatShowQuizFeedback(false);
          } else {
            // Session changed, do not show quiz
            setChatQuizGenerating(false);
            return;
          }
        } catch (err: any) {
          console.error('Failed to generate quiz:', err);
          setChatCountError('Failed to generate quiz');
        } finally {
          setChatQuizGenerating(false);
        }
      }
    } catch (err: any) {
      setChatCountError(err.message || 'Failed to fetch chat count');
    } finally {
      setChatCountLoading(false);
    }
  };

  // On session change or mount, fetch quiz progress (only if authenticated and sessionId exists)
  useEffect(() => {
    if (apiConfig.sessionId && isAuthenticated && apiConfig.sessionId.trim() !== '') {
      fetchQuizProgress(apiConfig.sessionId);
    }
  }, [apiConfig.sessionId, isAuthenticated]);

  // On quiz tracker button click, fetch quiz history
  const handleQuizTrackerClick = () => {
    if (apiConfig.sessionId && isAuthenticated && apiConfig.sessionId.trim() !== '') {
      fetchQuizHistory(apiConfig.sessionId);
      setShowQuizDropdown(true);
    }
  };

  // After quiz submission, refetch quiz progress
  const handleQuizSubmit = async (...args: any[]) => {
    // Existing quiz submission logic...
    if (apiConfig.sessionId && apiConfig.sessionId.trim() !== '') {
      await fetchQuizProgress(apiConfig.sessionId);
    }
  };

  // After each user message, fetch chat count and maybe trigger quiz
  const dispatchUserMessage = async (message: string) => {
    // Existing send message logic...
    if (apiConfig.sessionId && apiConfig.sessionId.trim() !== '') {
      await fetchChatCountAndMaybeTriggerQuiz(apiConfig.sessionId);
    }
  };





  // Show landing page if not authenticated
  if (!isAuthenticated) {
    return (
      <LandingPage onAuthSuccess={handleAuthSuccess} />
    );
  }

  return (
    <div className={`chat-app ${currentTheme} ${(currentWindow === 'chat' || currentWindow === 'learn') && sidebarHook.sidebarState.isOpen ? 'sidebar-open' : ''}`}>
      {/* Sidebar - show in both chat and learn windows */}
      {(currentWindow === 'chat' || currentWindow === 'learn') && (
        <Sidebar
          sidebarState={sidebarHook.sidebarState}
          setSidebarState={sidebarHook.setSidebarState}
          chatSessions={chatSessions}
          userProfile={profileHook.userProfile}
          profileModalState={profileHook.profileModalState}
          setProfileModalState={profileHook.setProfileModalState}
          onSessionSelect={(sessionId) => {
            if (currentWindow === 'learn') {
              setCurrentWindow('chat');
              setTimeout(() => handleSessionSelect(sessionId), 0);
            } else {
              handleSessionSelect(sessionId);
            }
          }}
          onNewChat={() => {
            if (currentWindow === 'learn') {
              setCurrentWindow('chat');
              setTimeout(() => handleNewChat(), 0);
            } else {
              handleNewChat();
            }
          }}
          onSessionDelete={handleSessionDelete}
          onProfileUpdate={profileHook.updateProfile}
          theme={currentTheme}
          apiConfig={apiConfig}
          isLoadingSessions={isLoadingSessions}
          sessionsError={sessionsError}
        />
      )}

      <div className={`chat-widget ${currentTheme} ${position}`}>
        {/* Session Expired Modal - rendered inside chat widget */}
        {showSessionExpiredModal && (
          <SessionExpiredModal
            isOpen={showSessionExpiredModal}
            onStayLoggedIn={handleSessionExpiredStayLoggedIn}
            onLogout={handleSessionExpiredLogout}
          />
        )}

        <div className="chat-header">
          <div className="header-left">
            {/* SidebarToggle - show in both chat and learn windows */}
            {(currentWindow === 'chat' || currentWindow === 'learn') ? (
              <SidebarToggle 
                isOpen={sidebarHook.sidebarState.isOpen}
                onClick={sidebarHook.toggleSidebar}
              />
            ) : (
              <div className="sidebar-toggle-placeholder" />
            )}
            <h3>💰 MoneyMentor</h3>
          </div>
          <div className="mode-navigation-centered desktop-only">
            <div className="mode-navigation-glass">
              <button
                className={`mode-btn ${currentWindow === 'chat' ? 'active' : ''}`}
                onClick={() => setCurrentWindow('chat')}
              >
                <span className="mode-icon">💬</span>
                <span className="mode-text">Chat</span>
              </button>
              <button 
                className={`mode-btn ${currentWindow === 'learn' ? 'active' : ''}`}
                onClick={() => setCurrentWindow('learn')}
              >
                <span className="mode-icon">🎓</span>
                <span className="mode-text">Learn</span>
              </button>
            </div>
          </div>
          <div className="header-spacer"></div>
          <button 
            onClick={handleLogout} 
            className="logout-btn" 
            title="Logout"
            disabled={isLoggingOut}
            style={{ opacity: isLoggingOut ? 0.6 : 1, cursor: isLoggingOut ? 'not-allowed' : 'pointer' }}
          >
            <LogoutRounded fontSize="small" />
            {isLoggingOut && <span style={{ marginLeft: '4px', fontSize: '12px' }}>...</span>}
          </button>
        </div>

        {/* Mobile Mode Navigation - positioned below header */}
        {currentWindow !== 'intro' && (
          <div className="mobile-mode-navigation">
            <div className="mode-navigation-glass">
              {/* Quiz Navigation - Only show when in quiz mode */}
              {(chatCourseQuiz || learnCourseQuiz) && (
                <>
                  <button
                    className="quiz-nav-btn quiz-back-btn"
                    onClick={() => {
                      if (chatCourseQuiz) {
                        chatWindow.handleCourseQuizNavigation('previous', chatCourseQuiz, chatCourseQuizAnswers);
                      } else if (learnCourseQuiz) {
                        learnWindow.handleCourseQuizNavigation('previous', learnCourseQuiz, learnCourseQuizAnswers);
                      }
                    }}
                    disabled={
                      !!(chatCourseQuiz && chatCourseQuiz.pageIndex === 0) ||
                      !!(learnCourseQuiz && learnCourseQuiz.pageIndex === 0)
                    }
                  >
                    <span className="quiz-nav-icon">←</span>
                    <span className="quiz-nav-text">Back</span>
                  </button>
                  
                  <div className="quiz-progress-indicator">
                    <span className="progress-text">
                      {chatCourseQuiz 
                        ? `${chatCourseQuiz.pageIndex + 1}/${chatCourseQuiz.totalPages}`
                        : learnCourseQuiz 
                        ? `${learnCourseQuiz.pageIndex + 1}/${learnCourseQuiz.totalPages}`
                        : '0/0'
                      }
                    </span>
                  </div>
                  
                  <button
                    className="quiz-nav-btn quiz-next-btn"
                    onClick={() => {
                      if (chatCourseQuiz) {
                        chatWindow.handleCourseQuizNavigation('next', chatCourseQuiz, chatCourseQuizAnswers);
                      } else if (learnCourseQuiz) {
                        learnWindow.handleCourseQuizNavigation('next', learnCourseQuiz, learnCourseQuizAnswers);
                      }
                    }}
                    disabled={
                      !!(chatCourseQuiz && chatCourseQuiz.pageIndex >= chatCourseQuiz.totalPages - 1) ||
                      !!(learnCourseQuiz && learnCourseQuiz.pageIndex >= learnCourseQuiz.totalPages - 1)
                    }
                  >
                    <span className="quiz-nav-text">Next</span>
                    <span className="quiz-nav-icon">→</span>
                  </button>
                </>
              )}
              
              {/* Regular Navigation - Show when not in quiz mode */}
              {!chatCourseQuiz && !learnCourseQuiz && (
                <>
                  <button
                    className={`mode-btn ${currentWindow === 'chat' ? 'active' : ''}`}
                    onClick={() => setCurrentWindow('chat')}
                  >
                    <span className="mode-icon">💬</span>
                    <span className="mode-text">Chat</span>
                  </button>
                  <button 
                    className={`mode-btn ${currentWindow === 'learn' ? 'active' : ''}`}
                    onClick={() => setCurrentWindow('learn')}
                  >
                    <span className="mode-icon">🎓</span>
                    <span className="mode-text">Learn</span>
                  </button>
                </>
              )}
            </div>
          </div>
        )}

        {/* Upload Progress Indicator Component */}
        <UploadProgressIndicator uploadProgress={uploadProgress} />

        {/* Uploaded Files Display Component - only show when there are files */}
        {uploadedFiles.length > 0 && (
        <UploadedFilesDisplay 
          uploadedFiles={uploadedFiles}
            onRemoveFile={handleChatRemoveFile}
        />
        )}

        {/* Windows Component */}
        <Windows
          currentWindow={currentWindow}
          onNavigateToChat={() => setCurrentWindow('chat')}
          onNavigateToLearn={() => setCurrentWindow('learn')}
          onNavigateToIntro={() => setCurrentWindow('intro')}
          isExpanded={true}
          hasUploads={uploadProgress.isUploading || uploadedFiles.length > 0}
          showQuizDropdown={showQuizDropdown}
          onToggleQuizDropdown={() => setShowQuizDropdown(prev => !prev)}
          onCloseQuizDropdown={() => setShowQuizDropdown(false)}
          quizTrackerRef={quizTrackerRef}
          chatQuizCorrectAnswered={chatQuizCorrectAnswered}
          chatQuizTotalAnswered={chatQuizTotalAnswered}
          chatQuizHistory={chatQuizHistory}
          QuizHistoryDropdown={QuizHistoryDropdown}
          onQuizTrackerClick={handleQuizTrackerClick}
          quizProgressLoading={quizProgressLoading}
          quizHistoryLoading={quizHistoryLoading}
          quizHistoryError={quizHistoryError}
          chatChildren={
            <div className="chat-window">
              {/* Chat Messages Container with Scrollbar */}
              <div className="chat-messages-container">
        <div className="chat-messages">
                {chatMessages.map((message) => (
            <div key={message.id} className={`message ${message.type} group ${message.metadata?.isCongratulations ? 'congratulations' : ''}`}>
                      {message.type === 'assistant' ? (
                        <BotMessage
                          content={message.content}
                          messageId={message.id}
                          onCopy={() => {
                            navigator.clipboard.writeText(message.content);
                          }}
                          isLastMessage={chatMessages.indexOf(message) === chatMessages.length - 1}
                          isGenerating={chatIsLoading}
                          showActions={true}
                        />
                      ) : message.type === 'system' ? (
                        <div className="message-content system-message">
                          {formatMessageContent(message.content)}
                        </div>
                      ) : (
              <div className="message-content">
                {formatMessageContent(message.content)}
              </div>
                      )}
              {/* Display buttons if present */}
              {message.metadata?.buttons && (
                <MessageButtons buttons={message.metadata.buttons} messageId={message.id} />
              )}
              {/* Display calculation result if present */}
              {message.metadata?.calculationResult && (
                <CalculationResult result={message.metadata.calculationResult} />
              )}

            </div>
          ))}

          {/* Shimmer Loading Components */}
          {chatQuizGenerating && (
            <ShimmerLoading type="quiz" theme={currentTheme} />
          )}
          {chatDiagnosticGenerating && (
            <ShimmerLoading type="diagnostic" theme={currentTheme} />
          )}
          {chatCourseGenerating && (
            <ShimmerLoading type="course" theme={currentTheme} />
          )}
          {chatCourseCompleting && (
            <ShimmerLoading type="course" theme={currentTheme} />
          )}
          {chatQuizSubmitting && (
            <ShimmerLoading type="quiz" theme={currentTheme} />
          )}
          {/* Diagnostic Test Component */}
          <DiagnosticTest
                  isDiagnosticMode={chatIsDiagnosticMode}
                  currentQuiz={chatCurrentDiagnosticQuiz}
                  showDiagnosticFeedback={chatShowDiagnosticFeedback}
                  diagnosticFeedback={chatDiagnosticFeedback}
                  diagnosticQuestionIndex={chatCurrentDiagnosticQuestionIndex}
                  diagnosticTotalQuestions={chatDiagnosticTotalQuestions}
                  onDiagnosticQuizAnswer={handleChatDiagnosticQuizAnswer}
                  onNextDiagnosticQuestion={() => handleNextDiagnosticQuestion(chatDiagnosticState, this.createDiagnosticHandlersProps())}
          />
          {/* Quiz Component */}
          <Quiz
                  currentQuiz={chatCurrentQuiz}
                  showQuizFeedback={chatShowQuizFeedback}
                  lastQuizAnswer={chatLastQuizAnswer}
                  isDiagnosticMode={chatIsDiagnosticMode}
                  onQuizAnswer={handleChatQuizAnswer}
          />
          {/* Course List Component */}
          <CourseList
                  showCourseList={chatShowCourseList}
                  availableCourses={chatAvailableCourses}
                  onStartCourse={handleChatStartCourse}
          />
          {/* Course Page Component (only for non-quiz pages) */}
          {chatCourseQuiz == null && chatCurrentCoursePage && (
          <CoursePageComponent
                  currentCoursePage={chatCurrentCoursePage}
                  onNavigateCoursePage={handleChatNavigateCoursePage}
                  onCompleteCourse={handleChatCompleteCourse}
          />
          )}
          {/* Course Quiz Component (for quiz pages) */}
          {chatCourseQuiz && (
          <CourseQuiz
                  courseQuiz={chatCourseQuiz}
                  courseQuizAnswers={chatCourseQuizAnswers}
                  onCourseQuizAnswerSelection={handleChatCourseQuizAnswerSelection}
                  onCourseQuizNavigation={handleChatCourseQuizNavigation}
                  onSubmitCourseQuiz={handleChatSubmitCourseQuiz}
                  areAllQuestionsAnswered={(answers) => areAllQuestionsAnswered(answers)}
                />
          )}



          <div ref={messagesEndRef} />
        </div>
              </div>
        {/* Chat Input Component */}
        <ChatInput
                inputValue={chatInputValue}
                isLoading={chatIsLoading}
          uploadProgress={uploadProgress}
          showCommandSuggestions={false}
          commandSuggestions={[]}
          showCommandMenu={false}
          availableCommands={[]}
          activeMode={activeMode}
                onInputChange={handleChatInputChange}
                onSendMessage={handleChatSendMessage}
                onFileUpload={handleChatFileUpload}
          onCommandSelect={() => {}}
          onToggleCommandMenu={() => {}}
          onCloseCommandMenu={() => {}}
                disabled={currentWindow === 'intro'}
              />
            </div>
          }
          learnChildren={
            <LearningCenter
              currentPage={learnCurrentPage}
              onPageChange={setLearnCurrentPage}
              selectedCourseKey={learnSelectedCourseKey}
              selectedCourseLabel={learnSelectedCourseLabel}
              isDiagnosticMode={learnIsDiagnosticMode}
              currentDiagnosticQuiz={learnDiagnosticState.test?.questions[learnDiagnosticState.currentQuestionIndex] || null}
              showDiagnosticFeedback={learnShowDiagnosticFeedback}
              diagnosticFeedback={learnDiagnosticFeedback}
              diagnosticQuestionIndex={learnDiagnosticState.currentQuestionIndex}
              diagnosticTotalQuestions={learnDiagnosticState.test?.questions.length || 0}
              diagnosticState={learnDiagnosticState}
              onDiagnosticQuizAnswer={handleLearnDiagnosticQuizAnswer}
              onCompleteDiagnosticTest={handleLearnCompleteDiagnosticTest}
              setDiagnosticState={setLearnDiagnosticState}
              setShowDiagnosticFeedback={setLearnShowDiagnosticFeedback}
              setDiagnosticFeedback={setLearnDiagnosticFeedback}
              onBackToCourses={handleLearnBackToCourses}
              availableCourses={learnAvailableCourses}
              currentCoursePage={learnCurrentCoursePage}
              currentCourse={learnCurrentCourse}
              courseQuiz={learnCourseQuiz}
              courseQuizAnswers={learnCourseQuizAnswers}
              diagnosticGenerating={learnDiagnosticGenerating}
              courseGenerating={learnCourseGenerating}
              courseCompleting={learnCourseCompleting}
              quizSubmitting={learnQuizSubmitting}
              courseGenerationLoading={learnCourseGenerationLoading}
              onStartDiagnosticTest={(courseKey) => {
                // Find course label
                const course = [
                  { key: 'money-goals-mindset', label: 'Money, Goals and Mindset' },
                  { key: 'budgeting-saving', label: 'Budgeting and Saving' },
                  { key: 'college-planning-saving', label: 'College Planning and Saving' },
                  { key: 'earning-income-basics', label: 'Earning and Income Basics' },
                ].find(c => c.key === courseKey);
                
                setLearnSelectedCourseKey(courseKey);
                setLearnSelectedCourseLabel(course?.label || '');
                learnWindow.handleStartDiagnosticTest(courseKey);
              }}
              onStartCourse={handleLearnStartCourse}
              onNavigateCoursePage={handleLearnNavigateCoursePage}
              onCompleteCourse={handleLearnCompleteCourse}
              onCourseQuizAnswerSelection={handleLearnCourseQuizAnswerSelection}
              onCourseQuizNavigation={handleLearnCourseQuizNavigation}
              onSubmitCourseQuiz={handleLearnSubmitCourseQuiz}
              areAllQuestionsAnswered={areAllQuestionsAnswered}
              theme={currentTheme}
            />
          }
        />
      </div>
    </div>
  );
}; 