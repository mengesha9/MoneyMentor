import { ChatResponse, DiagnosticTest, QuizSession, QuizQuestion, QuizResponse } from '../../types';
import Cookies from 'js-cookie';

export interface ApiConfig {
  apiUrl: string;
  userId: string;
  sessionId: string;
}

// const BACKEND_URL = 'http://localhost:8080';
// const BACKEND_URL = 'https://backend-647308514289.us-central1.run.app';
const BACKEND_URL = 'http://localhost:8000';  // Use local backend for development
// const BACKEND_TWO_URL = 'http://localhost:8000';
const BACKEND_TWO_URL = 'https://backend-2-647308514289.us-central1.run.app';

// Helper to get token from cookies
const getAuthToken = () => Cookies.get('auth_token');

// Helper to add Authorization header if token exists
const withAuth = (headers: Record<string, string> = {}) => {
  const token = getAuthToken();
  return token ? { ...headers, Authorization: `Bearer ${token}` } : headers;
};

/**
 * Make an authenticated API request with automatic token refresh
 */
export const makeAuthenticatedRequest = async (
  url: string,
  options: RequestInit = {}
): Promise<Response> => {
  // Add auth header
  const headers = withAuth(options.headers as Record<string, string> || {});
  
  // Make the request
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...headers
    }
  });

  // If we get a 401, try to refresh the token and retry once
  if (response.status === 401) {
    try {
      const refreshTokenValue = Cookies.get('refresh_token');
      if (refreshTokenValue) {
        const refreshResult = await refreshToken(refreshTokenValue);
        
        if (refreshResult && refreshResult.access_token) {
          // Update the stored token - match backend configuration
          Cookies.set('auth_token', refreshResult.access_token, { expires: 1/24 }); // 60 minutes
          
          // Retry the original request with the new token
          const newHeaders = {
            ...headers,
            Authorization: `Bearer ${refreshResult.access_token}`
          };
          
          return await fetch(url, {
            ...options,
            headers: {
              'Content-Type': 'application/json',
              ...newHeaders
            }
          });
        }
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      // If refresh fails, clear session and throw error
      Cookies.remove('auth_token');
      Cookies.remove('refresh_token');
      localStorage.removeItem('auth_token_expires');
      localStorage.removeItem('moneymentor_user_id');
      throw new Error('Authentication expired. Please log in again.');
    }
  }

  return response;
};

// Register API
export const registerUser = async (email: string, password: string, first_name: string, last_name: string): Promise<any> => {
  const response = await fetch(`${BACKEND_URL}/api/user/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, first_name, last_name })
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Registration failed');
  }
  
  return response.json();
};

// Login API
export const loginUser = async (email: string, password: string): Promise<any> => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
  
  try {
    const response = await fetch(`${BACKEND_URL}/api/user/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Login failed');
    }
    
    return response.json();
  } catch (error: any) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Login request timed out. Please try again.');
    }
    throw error;
  }
};

// Refresh token API
export const refreshToken = async (refresh_token: string): Promise<any> => {
  const response = await fetch(`${BACKEND_URL}/api/user/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token })
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Token refresh failed');
  }
  
  return response.json();
};

// Logout API
export const logoutUser = async (refresh_token: string): Promise<any> => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
  
  try {
    const response = await fetch(`${BACKEND_URL}/api/user/logout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token }),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Logout failed');
    }
    
    return response.json();
  } catch (error: any) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      // Logout timed out, but we should still clear local storage
      console.warn('Logout request timed out, clearing local session');
      return { message: 'Logged out (timeout)' };
    }
    throw error;
  }
};

// Chat API calls - Using port 8000
export const sendChatMessage = async (
  config: ApiConfig,
  message: string
): Promise<ChatResponse> => {
  const response = await makeAuthenticatedRequest(`${BACKEND_URL}/api/chat/message/stream`, {
    method: 'POST',
    body: JSON.stringify({
      query: message,
      session_id: config.sessionId
    })
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to send message');
  }

  return response.json();
};

// Streaming chat API call for raw token streaming
export const sendChatMessageStream = async (
  config: ApiConfig,
  message: string,
  onChunk: (chunk: string) => void,
  onComplete: (fullResponse: ChatResponse) => void,
  onError: (error: Error) => void
): Promise<void> => {
  try {
    // Validate input parameters
    if (!message || !message.trim()) {
      throw new Error('Query cannot be empty');
    }
    
    if (!config.sessionId || !config.sessionId.trim()) {
      throw new Error('Session ID cannot be empty');
    }

    const response = await fetch(`${BACKEND_URL}/api/chat/message/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...withAuth()
      },
      body: JSON.stringify({
        query: message.trim(),
        session_id: config.sessionId.trim()
      })
    });

    // Handle different response status codes
    if (response.status === 422) {
      throw new Error('Invalid request: Please check your input and try again.');
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to send message: ${response.status} ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let fullResponse = '';
    let hasReceivedFirstChunk = false;
    let errorDetected = false;

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        break;
      }

      // Decode the chunk
      const chunk = decoder.decode(value, { stream: true });
      
      // Check for error responses (even with 200 status)
      if (chunk.includes('"type": "error"') || chunk.includes('error')) {
        errorDetected = true;
        try {
          // Try to parse the error data
          const lines = chunk.split('\n');
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const jsonStr = line.replace('data: ', '');
              try {
                const errorData = JSON.parse(jsonStr);
                if (errorData.type === 'error') {
                  throw new Error(errorData.message || 'An error occurred while processing your request.');
                }
              } catch (parseError) {
                // Continue checking other lines
              }
            }
          }
          // If we can't parse specific error, throw generic error
          throw new Error('An error occurred while processing your request. Please try again.');
        } catch (parseError) {
          // If we can't parse the error, just throw the raw chunk
          throw new Error('An error occurred while processing your request.');
        }
      }
      
      // Add to full response
      fullResponse += chunk;
      
      // Mark that we've received the first chunk
      if (!hasReceivedFirstChunk) {
        hasReceivedFirstChunk = true;
      }
      
      // Send the chunk to the UI for real-time updates
      onChunk(chunk);
    }

    // If we detected an error but didn't throw, handle it now
    if (errorDetected) {
      throw new Error('An error occurred while processing your request. Please try again.');
    }

    // Create final response object
    const finalResponse: ChatResponse = {
      message: fullResponse,
      session_id: config.sessionId,
      quiz: null
    };

    // Call completion handler
    onComplete(finalResponse);

  } catch (error) {
    onError(error instanceof Error ? error : new Error('Unknown error'));
  }
};

// Quiz API calls - Using port 3000
export const initializeQuizSession = async (
  config: ApiConfig
): Promise<QuizSession> => {
  const response = await fetch(`${BACKEND_TWO_URL}/api/quiz/session`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      ...withAuth()
    },
    body: JSON.stringify({ 
      userId: config.userId, 
      sessionId: config.sessionId 
    })
  });

  if (!response.ok) {
    throw new Error('Failed to initialize quiz session');
  }

  const data = await response.json();
  return data.data;
};

export const loadDiagnosticTest = async (
  apiUrl: string
): Promise<DiagnosticTest> => {
  const response = await fetch(`${BACKEND_TWO_URL}/api/quiz/diagnostic`, {
    headers: withAuth()
  });
  
  if (!response.ok) {
    throw new Error('Failed to load diagnostic test');
  }

  const data = await response.json();
  return data.data;
};

export const completeDiagnosticTest = async (
  config: ApiConfig,
  score: number
): Promise<any> => {
  const response = await fetch(`${BACKEND_TWO_URL}/api/quiz/complete-diagnostic`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      ...withAuth()
    },
    body: JSON.stringify({ 
      userId: config.userId, 
      sessionId: config.sessionId, 
      score 
    })
  });

  if (!response.ok) {
    throw new Error('Failed to complete diagnostic test');
  }

  const data = await response.json();
  return data.data;
};

export const logQuizAnswer = async (
  config: ApiConfig,
  quizId: string,
  selectedOption: number,
  correct: boolean,
  topicTag: string
): Promise<void> => {
  // Convert selectedOption number to letter (0->A, 1->B, 2->C, 3->D)
  const optionLetters = ['A', 'B', 'C', 'D'];
  const selectedLetter = optionLetters[selectedOption] || 'A';
  
  // Use Python backend for Google Sheets logging
  const response = await fetch(`${BACKEND_URL}/api/quiz/submit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...withAuth()
    },
    body: JSON.stringify({
      user_id: config.userId,
      quiz_type: "micro",
      session_id: config.sessionId,
      responses: [
        {
          quiz_id: quizId,
          selected_option: selectedLetter,
          correct: correct,
          topic: topicTag
        }
      ]
    })
  });

  if (!response.ok) {
    throw new Error('Failed to log quiz answer');
  }
};

// Course API calls - Using new course service endpoints
export const getAvailableCourses = async (
  config: ApiConfig
): Promise<any> => {
  // Use makeAuthenticatedRequest instead of direct fetch to enable automatic token refresh
  const response = await makeAuthenticatedRequest(`${BACKEND_URL}/api/course/user/${config.userId}/sessions`, {
    method: 'GET'
  });

  if (!response.ok) {
    throw new Error('Failed to fetch courses');
  }

  const data = await response.json();
  return data.data;
};

export const startCourse = async (
  config: ApiConfig,
  courseId: string
): Promise<any> => {
  // Use makeAuthenticatedRequest instead of direct fetch to enable automatic token refresh
  const response = await makeAuthenticatedRequest(`${BACKEND_URL}/api/course/start`, {
    method: 'POST',
    body: JSON.stringify({ 
      user_id: config.userId, 
      session_id: config.sessionId, 
      course_id: courseId 
    })
  });

  if (!response.ok) {
    throw new Error('Failed to start course');
  }

  return response.json();
};

export const navigateCoursePage = async (
  config: ApiConfig,
  courseId: string,
  pageIndex: number
): Promise<any> => {
  console.log('🌐 navigateCoursePage API call:', { courseId, pageIndex, config });
  
  try {
    // Use makeAuthenticatedRequest instead of direct fetch to enable automatic token refresh
    const response = await makeAuthenticatedRequest(`${BACKEND_URL}/api/course/navigate`, {
      method: 'POST',
      body: JSON.stringify({ 
        user_id: config.userId,
        session_id: config.sessionId,
        course_id: courseId,
        page_index: pageIndex 
      })
    });

    console.log('📡 navigateCoursePage response status:', response.status);
    console.log('📡 navigateCoursePage response headers:', Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ navigateCoursePage failed:', response.status, errorText);
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    const data = await response.json();
    console.log('✅ navigateCoursePage success:', data);
    return data;
  } catch (error) {
    console.error('🚨 navigateCoursePage error:', error);
    throw error;
  }
};

export const submitCourseQuiz = async (
  config: ApiConfig,
  courseId: string,
  pageIndex: number,
  selectedOption: string,
  correct: boolean
): Promise<any> => {
  // Use makeAuthenticatedRequest instead of direct fetch to enable automatic token refresh
  const response = await makeAuthenticatedRequest(`${BACKEND_URL}/api/course/quiz/submit`, {
    method: 'POST',
    body: JSON.stringify({ 
      user_id: config.userId,
      session_id: config.sessionId,
      course_id: courseId,
      page_index: pageIndex,
      selected_option: selectedOption,
      correct
    })
  });

  if (!response.ok) {
    throw new Error('Failed to submit course quiz');
  }

  return response.json();
};

export const completeCourse = async (
  config: ApiConfig,
  courseId: string
): Promise<any> => {
  // Use makeAuthenticatedRequest instead of direct fetch to enable automatic token refresh
  const response = await makeAuthenticatedRequest(`${BACKEND_URL}/api/course/complete`, {
    method: 'POST',
    body: JSON.stringify({ 
      user_id: config.userId,
      session_id: config.sessionId,
      course_id: courseId
    })
  });

  if (!response.ok) {
    throw new Error('Failed to complete course');
  }

  return response.json();
};

export const getCourseDetails = async (
  config: ApiConfig,
  courseId: string
): Promise<any> => {
  // Use makeAuthenticatedRequest instead of direct fetch to enable automatic token refresh
  const response = await makeAuthenticatedRequest(`${BACKEND_URL}/api/course/${courseId}`, {
    method: 'GET'
  });

  if (!response.ok) {
    throw new Error('Failed to get course details');
  }

  return response.json();
};

// Content upload API calls - Using port 3000
export const uploadFile = async (
  config: ApiConfig,
  file: File
): Promise<any> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('userId', config.userId);
  formData.append('sessionId', config.sessionId);

  const response = await fetch(`${BACKEND_TWO_URL}/api/content/upload`, {
    method: 'POST',
    headers: withAuth(),
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(errorData.error || 'Upload failed');
  }

  return response.json();
};

export const removeFile = async (
  config: ApiConfig,
  fileName: string
): Promise<void> => {
  const response = await fetch(`${BACKEND_TWO_URL}/api/content/remove`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      ...withAuth()
    },
    body: JSON.stringify({ 
      userId: config.userId, 
      sessionId: config.sessionId, 
      fileName 
    })
  });

  if (!response.ok) {
    throw new Error('Failed to remove file');
  }
};

// Diagnostic API functions - Using port 3000
export const startDiagnosticTest = async (
  config: ApiConfig
): Promise<any> => {
  const response = await fetch(`${BACKEND_TWO_URL}/api/quiz/start-diagnostic`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      ...withAuth()
    },
    body: JSON.stringify({ 
      userId: config.userId, 
      sessionId: config.sessionId 
    })
  });

  if (!response.ok) {
    throw new Error('Failed to start diagnostic test');
  }

  const data = await response.json();
  return data.data;
};

export const getDiagnosticQuestion = async (
  apiUrl: string,
  questionIndex: number
): Promise<any> => {
  const response = await fetch(`${BACKEND_TWO_URL}/api/quiz/diagnostic/question/${questionIndex}`, {
    headers: withAuth()
  });
  
  if (!response.ok) {
    throw new Error('Failed to get diagnostic question');
  }

  const data = await response.json();
  return data.data;
};

// New: Generate Diagnostic Quiz (POST /api/quiz/generate)
export const generateDiagnosticQuiz = async (
  config: ApiConfig,
  topic?: string
): Promise<{ questions: QuizQuestion[]; quizId: string }> => {
  const requestBody: any = {
    session_id: config.sessionId,
    quiz_type: 'diagnostic'
  };
  
  // Add topic if provided
  if (topic) {
    requestBody.topic = topic;
  }

  const response = await makeAuthenticatedRequest(`${BACKEND_URL}/api/quiz/generate`, {
    method: 'POST',
    body: JSON.stringify(requestBody)
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to generate diagnostic quiz');
  }

  const data = await response.json();
  // Map backend format to local QuizQuestion[]
  const questions = data.questions.map((q: any) => ({
    id: '', // Backend does not provide id, can generate if needed
    question: q.question,
    options: Object.values(q.choices),
    correctAnswer: ['a', 'b', 'c', 'd'].indexOf(q.correct_answer.toLowerCase()),
    explanation: q.explanation,
    topicTag: q.topic || '',
    difficulty: 'medium', // Default or map if provided
  }));
  return { questions, quizId: data.quiz_id };
};

// New: Generate Micro Quiz (POST /api/quiz/generate)
export const generateMicroQuiz = async (
  config: ApiConfig
): Promise<{ questions: QuizQuestion[]; quizId: string }> => {
  const requestBody = {
    session_id: config.sessionId,
    quiz_type: 'micro'
  };

  const response = await makeAuthenticatedRequest(`${BACKEND_URL}/api/quiz/generate`, {
    method: 'POST',
    body: JSON.stringify(requestBody)
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to generate micro quiz');
  }

  const data = await response.json();
  // Map backend format to local QuizQuestion[]
  const questions = data.questions.map((q: any) => ({
    id: '', // Backend does not provide id, can generate if needed
    question: q.question,
    options: Object.values(q.choices),
    correctAnswer: ['a', 'b', 'c', 'd'].indexOf(q.correct_answer.toLowerCase()),
    explanation: q.explanation,
    topicTag: q.topic || '',
    difficulty: 'medium', // Default or map if provided
  }));
  return { questions, quizId: data.quiz_id };
};

// New: Submit Diagnostic Quiz (POST /api/quiz/submit)
export const submitDiagnosticQuiz = async (
  config: ApiConfig,
  quizId: string,
  responses: QuizResponse[],
  userId: string,
  selectedCourseType?: string
): Promise<any> => {
  console.log('🔍 submitDiagnosticQuiz CALLED WITH:');
  console.log('  📋 config:', config);
  console.log('  📋 config.userId:', config.userId);
  console.log('  📋 config.sessionId:', config.sessionId);
  console.log('  🆔 quizId:', quizId);
  console.log('  📝 responses:', responses);
  console.log('  👤 userId:', userId);
  console.log('  📊 responses type:', typeof responses);
  console.log('  📊 responses length:', responses?.length);
  console.log('  📊 responses[0]:', responses?.[0]);
  
  const requestBody = {
    user_id: userId,
    quiz_type: 'diagnostic',
    session_id: config.sessionId,
    selected_course_type: selectedCourseType,
    responses: responses
  };

  console.log('📤 Sending diagnostic quiz data to backend:', {
    url: `${BACKEND_URL}/api/quiz/submit`,
    method: 'POST',
    body: requestBody,
    authToken: getAuthToken() ? 'Present' : 'Missing'
  });

  // Add detailed logging of the request body
  console.log('🔍 DETAILED REQUEST BODY:', JSON.stringify(requestBody, null, 2));
  console.log('🔍 RESPONSES ARRAY:', JSON.stringify(requestBody.responses, null, 2));
  console.log('🔍 FIRST RESPONSE:', JSON.stringify(requestBody.responses[0], null, 2));
  console.log('🔍 USER_ID BEING SENT:', requestBody.user_id);
  console.log('🔍 USER_ID TYPE:', typeof requestBody.user_id);
  console.log('🔍 SELECTED_COURSE_TYPE:', requestBody.selected_course_type);
  console.log('🔍 SELECTED_COURSE_TYPE TYPE:', typeof requestBody.selected_course_type);

  try {
    // Use makeAuthenticatedRequest instead of direct fetch to enable automatic token refresh
    const response = await makeAuthenticatedRequest(`${BACKEND_URL}/api/quiz/submit`, {
      method: 'POST',
      body: JSON.stringify(requestBody) // Use real quiz data
    });

    console.log('📥 Backend response status:', response.status, response.statusText);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Backend error response:', errorText);
      throw new Error(`Failed to submit diagnostic quiz: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log('✅ Backend response data:', data);
    console.log('🔍 Backend response structure:');
    console.log('  📊 Success:', data.success);
    console.log('  💬 Message:', data.message);
    console.log('  📝 Data field:', data.data);
    console.log('  🤖 AI Generated Course:', data.data?.ai_generated_course);
    console.log('  📚 Recommended Course ID:', data.data?.recommended_course_id);
    
    // Return the data field if it exists, otherwise return the full response
    return data.data || data;
  } catch (error) {
    console.error('❌ Error submitting diagnostic quiz:', error);
    throw error;
  }
}; 

// New: Submit Micro Quiz (POST /api/quiz/submit)
export const submitMicroQuiz = async (
  config: ApiConfig,
  quizId: string,
  question: QuizQuestion,
  selectedOption: number,
  correct: boolean,
  userId: string
): Promise<any> => {
  // Use makeAuthenticatedRequest instead of direct fetch to enable automatic token refresh
  const response = await makeAuthenticatedRequest(`${BACKEND_URL}/api/quiz/submit`, {
    method: 'POST',
    body: JSON.stringify({
      user_id: userId,
      quiz_type: 'micro',
      session_id: config.sessionId,
      responses: [
        {
          quiz_id: quizId,
          selected_option: String.fromCharCode(65 + selectedOption), // 'A', 'B', 'C', 'D'
          correct,
          topic: question.topicTag || '',
          // Include full question data for proper storage
          question_data: {
            question: question.question,
            choices: question.options.reduce((acc, option, idx) => {
              acc[String.fromCharCode(65 + idx)] = option; // 'A': 'option text', 'B': 'option text', etc.
              return acc;
            }, {} as Record<string, string>),
            correct_answer: String.fromCharCode(65 + question.correctAnswer), // 'A', 'B', 'C', 'D'
            explanation: question.explanation || ''
          },
          explanation: question.explanation || '',
          correct_answer: String.fromCharCode(65 + question.correctAnswer)
        }
      ]
    })
  });
  
  if (!response.ok) {
    throw new Error('Failed to submit micro quiz');
  }
  return response.json();
};

// User Profile API calls
export const getUserProfile = async (): Promise<any> => {
  const response = await makeAuthenticatedRequest(`${BACKEND_URL}/api/user/profile`);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to get profile');
  }
  
  return response.json();
};

export const updateUserProfile = async (profileData: {
  first_name?: string;
  last_name?: string;
  email?: string;
}): Promise<any> => {
  const response = await makeAuthenticatedRequest(`${BACKEND_URL}/api/user/profile`, {
    method: 'PUT',
    body: JSON.stringify(profileData)
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to update profile');
  }
  
  return response.json();
};

export const changeUserPassword = async (currentPassword: string, newPassword: string): Promise<any> => {
  const response = await makeAuthenticatedRequest(`${BACKEND_URL}/api/user/password`, {
    method: 'PUT',
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword
    })
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to change password');
  }
  
  return response.json();
};

export const deleteUserAccount = async (currentPassword: string): Promise<any> => {
  const response = await makeAuthenticatedRequest(`${BACKEND_URL}/api/user/account`, {
    method: 'DELETE',
    body: JSON.stringify({
      current_password: currentPassword
    })
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to delete account');
  }
  
  return response.json();
}; 

// Chat Session Management API calls
export const getAllUserSessions = async (config: ApiConfig): Promise<any> => {
  const response = await makeAuthenticatedRequest(`${BACKEND_URL}/api/chat/history/`, {
    method: 'GET'
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch chat sessions');
  }

  return response.json();
};

export const getSessionHistory = async (config: ApiConfig, sessionId: string): Promise<any> => {
  const response = await makeAuthenticatedRequest(`${BACKEND_URL}/api/chat/history/${sessionId}`, {
    method: 'GET'
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch session history');
  }

  return response.json();
};

export const deleteSession = async (config: ApiConfig, sessionId: string): Promise<any> => {
  const response = await makeAuthenticatedRequest(`${BACKEND_URL}/api/chat/session/${sessionId}`, {
    method: 'DELETE'
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to delete session');
  }

  return response.json();
};

// Get session quiz progress (x/y correct/total)
export const getSessionQuizProgress = async (config: ApiConfig, sessionId: string): Promise<{ correct_answers: number; total_quizzes: number; score_percentage: number }> => {
  const response = await makeAuthenticatedRequest(`${BACKEND_URL}/api/quiz/progress/session/${sessionId}`, {
    method: 'GET'
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch session quiz progress');
  }
  return response.json();
};

// Get session quiz history (list of quizzes for this session)
export const getSessionQuizHistory = async (config: ApiConfig, sessionId: string): Promise<any> => {
  const response = await makeAuthenticatedRequest(`${BACKEND_URL}/api/quiz/history/session/${sessionId}`, {
    method: 'GET'
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch session quiz history');
  }
  return response.json();
};

// Get all quiz history for the user
export const getAllQuizHistory = async (config: ApiConfig): Promise<any> => {
  const response = await makeAuthenticatedRequest(`${BACKEND_URL}/api/quiz/history`, {
    method: 'GET'
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch quiz history');
  }
  return response.json();
};

// Get session chat count (number of user messages, should_generate_quiz)
export const getSessionChatCount = async (config: ApiConfig, sessionId: string): Promise<{ chat_count: number; should_generate_quiz: boolean; messages_until_quiz: number }> => {
  const response = await makeAuthenticatedRequest(`${BACKEND_URL}/api/chat/session/${sessionId}/chat-count`, {
    method: 'GET'
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch session chat count');
  }
  return response.json();
};