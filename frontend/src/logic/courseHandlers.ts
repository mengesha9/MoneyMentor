import { ChatMessage, Course, CoursePage } from '../types';
import { 
  ApiConfig,
  createSystemMessage,
  formatCourseStartMessage,
  formatCourseCompletionMessage,
  getAvailableCourses,
  startCourse,
  navigateCoursePage,
  submitCourseQuiz,
  formatQuizResultMessage,
  resetCourseQuizState,
  initializeCourseQuiz,
  initializeCourseQuizAnswers,
  CourseQuizState,
  CourseQuizAnswers,
  completeCourse,
  getCourseDetails
} from '../utils/chatWidget';
import { createAssistantMessage } from '../utils/chatWidget/messageUtils';

export interface CourseHandlersProps {
  apiConfig: ApiConfig;
  sessionIds: { userId: string; sessionId: string };
  addMessage: (message: any) => void;
  setIsLoading: (loading: boolean) => void;
  setCourseGenerating?: (loading: boolean) => void;
  setCourseCompleting?: (loading: boolean) => void;
  closeCurrentDisplays: () => void;
  setAvailableCourses: (courses: Course[]) => void;
  setShowCourseList: (show: boolean) => void;
  setCurrentCoursePage: (page: CoursePage | null) => void;
  setCurrentCourse: (course: Course | null) => void;
  setCourseQuiz: (quiz: any) => void;
  setCourseQuizAnswers: (answers: any) => void;
  removeIntroMessage: (pattern: string) => void;
}

// Utility to normalize backend quiz_data to frontend format
function normalizeQuizQuestion(raw: any): any {
  if (!raw) return null;
  // If already in frontend format, return as is
  if (Array.isArray(raw.options)) return raw;
  // Convert choices object to options array
  if (raw.choices && typeof raw.choices === 'object') {
    const options = Object.values(raw.choices);
    // Map correct_answer (a/b/c/d) to index
    const correctAnswer = ['a', 'b', 'c', 'd'].indexOf(raw.correct_answer);
    return {
      id: raw.id || '',
      question: raw.question,
      options,
      correctAnswer,
      explanation: raw.explanation || '',
      topicTag: raw.topic || '',
      difficulty: raw.difficulty || 'medium',
    };
  }
  return raw;
}

export const handleCoursesList = async (props: CourseHandlersProps) => {
  const {
    apiConfig,
    sessionIds,
    addMessage,
    setIsLoading,
    closeCurrentDisplays,
    setAvailableCourses,
    setShowCourseList,
    removeIntroMessage
  } = props;

  closeCurrentDisplays();
  setIsLoading(true);
  
  // Add intro message while loading
  const coursesMessage = createSystemMessage(
    '📚 **Available Courses**\n\nHere are all the courses available for you:',
    sessionIds.sessionId,
    sessionIds.userId
  );
  addMessage(coursesMessage);
  
  try {
    const response = await getAvailableCourses(apiConfig);
    
    // Ensure the response matches the Course interface
    const courses = Array.isArray(response) ? response : [];
    setAvailableCourses(courses);
    setShowCourseList(true);
    
    // Remove the intro message once courses are loaded
    removeIntroMessage('📚 **Available Courses**');
    
  } catch (error) {
    console.error('Error fetching courses:', error);
    const errorMessage = createSystemMessage(
      'Failed to fetch courses. Please try again later.',
      sessionIds.sessionId,
      sessionIds.userId
    );
    addMessage(errorMessage);
  } finally {
    setIsLoading(false);
  }
};

export const handleStartCourse = async (
  courseId: string,
  props: CourseHandlersProps
) => {
  const {
    apiConfig,
    sessionIds,
    addMessage,
    setIsLoading,
    setCourseGenerating,
    closeCurrentDisplays,
    setCurrentCoursePage,
    setCurrentCourse,
    setCourseQuiz,
    setCourseQuizAnswers
  } = props;

  try {
    setIsLoading(true);
    closeCurrentDisplays();
    
    // Show shimmer loading for course generation
    if (setCourseGenerating) {
      setCourseGenerating(true);
    }
    
    // Start the course with retry mechanism
    let result;
    let retryCount = 0;
    const maxRetries = 3;
    
    while (retryCount < maxRetries) {
      try {
        result = await startCourse(apiConfig, courseId);
        if (result.success) {
          break; // Success, exit retry loop
        } else if (result.message && (result.message.includes('not found') || result.message.includes('properly registered'))) {
          // Course might still be registering, wait and retry
          if (retryCount < maxRetries - 1) {
            await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1))); // Exponential backoff
            retryCount++;
            continue;
          }
        }
        throw new Error(result.message || 'Failed to start course');
      } catch (error) {
        if (retryCount < maxRetries - 1 && error instanceof Error && 
            (error.message.includes('not found') || error.message.includes('properly registered'))) {
          await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1))); // Exponential backoff
          retryCount++;
          continue;
        }
        throw error;
      }
    }
    
    if (result.success) {
      // Get course details
      const courseDetails = await getCourseDetails(apiConfig, courseId);
      
      if (courseDetails.success) {
        const courseData = courseDetails.data;
        
        // Set current course
        const course: Course = {
          id: courseData.id,
          title: courseData.title,
          description: courseData.lesson_overview,
          difficulty: courseData.course_level as 'beginner' | 'intermediate' | 'advanced',
          topicTag: courseData.topic,
          estimatedTime: courseData.estimated_length,
          pages: [], // Will be populated as user navigates
          quizQuestions: []
        };
        
        setCurrentCourse(course);
        
        // Always fetch the first page (page 0) when starting a course
        try {
          console.log('📚 Fetching first page for course:', courseId);
          console.log('🔍 API Config:', { userId: apiConfig.userId, sessionId: apiConfig.sessionId });
          console.log('🌐 Backend URL:', `${apiConfig.backendUrl}/api/course/navigate`);
          
          const firstPageResult = await navigateCoursePage(apiConfig, courseId, 0);
          console.log('📄 First page API result:', firstPageResult);
          
          if (firstPageResult.success && firstPageResult.data && firstPageResult.data.current_page) {
            const pageData = firstPageResult.data.current_page;
            console.log('✅ First page fetched successfully:', pageData);
            console.log('📖 Page details:', {
              id: pageData.id,
              title: pageData.title,
              pageType: pageData.page_type,
              hasContent: !!pageData.content,
              contentLength: pageData.content?.length || 0
            });
            
            if (pageData.page_type === 'quiz' && pageData.quiz_data) {
              // Quiz page: initialize course quiz state
              const quizQuestions = Array.isArray(pageData.quiz_data)
                ? pageData.quiz_data.map(normalizeQuizQuestion)
                : [normalizeQuizQuestion(pageData.quiz_data)];
              const courseQuizState = {
                questions: quizQuestions,
                currentQuestion: 0,
                score: 0,
                attempts: 0,
                pageIndex: pageData.page_index,
                totalPages: pageData.total_pages || 10 // Default to 10 pages
              };
              
              setCurrentCoursePage(null);
              setCourseQuiz(courseQuizState);
              setCourseQuizAnswers(initializeCourseQuizAnswers(quizQuestions.length));
              console.log('🎯 Quiz page initialized:', courseQuizState);
              
            } else {
              // Content page
              const page: CoursePage = {
                id: pageData.id,
                title: pageData.title,
                content: pageData.content,
                pageNumber: pageData.page_index + 1,
                totalPages: pageData.total_pages || 10, // Default to 10 pages if not provided
                pageType: pageData.page_type,
                quizData: pageData.quiz_data
              };
              setCurrentCoursePage(page);
              console.log('📖 Content page set successfully:', {
                pageNumber: page.pageNumber,
                totalPages: page.totalPages,
                title: page.title,
                hasContent: !!page.content
              });
            }
          } else {
            console.warn('⚠️ First page fetch failed, using fallback data');
            console.warn('❌ API Response:', firstPageResult);
            console.warn('🔍 Response structure:', {
              success: firstPageResult.success,
              hasData: !!firstPageResult.data,
              hasCurrentPage: !!firstPageResult.data?.current_page,
              responseKeys: Object.keys(firstPageResult)
            });
            // Fallback: create a basic first page
            const fallbackPage: CoursePage = {
              id: 'fallback',
              title: 'Welcome to Your Course',
              content: courseData.lesson_overview || 'Course content is loading...',
              pageNumber: 1,
              totalPages: 10,
              pageType: 'content',
              quizData: null
            };
            setCurrentCoursePage(fallbackPage);
            console.log('🔄 Fallback page created:', fallbackPage);
          }
        } catch (pageError) {
          console.error('❌ Error fetching first page:', pageError);
          console.error('🚨 Error details:', {
            message: pageError instanceof Error ? pageError.message : 'Unknown error',
            stack: pageError instanceof Error ? pageError.stack : 'No stack trace',
            errorType: pageError.constructor.name
          });
          // Fallback: create a basic first page
          const fallbackPage: CoursePage = {
            id: 'fallback',
            title: 'Welcome to Your Course',
            content: courseData.lesson_overview || 'Course content is loading...',
            pageNumber: 1,
            totalPages: 10,
            pageType: 'content',
            quizData: null
          };
          setCurrentCoursePage(fallbackPage);
          console.log('🔄 Fallback page created after error:', fallbackPage);
        }
      } else {
        throw new Error(courseDetails.message || 'Failed to get course details');
      }
    } else {
      throw new Error(result.message || 'Failed to start course');
    }
    
  } catch (error) {
    console.error('Error starting course:', error);
    const errorMessage = createSystemMessage(
      'Failed to start course. Please try again later.',
      sessionIds.sessionId,
      sessionIds.userId
    );
    addMessage(errorMessage);
  } finally {
    setIsLoading(false);
    if (setCourseGenerating) {
      setCourseGenerating(false);
    }
  }
};

export const handleNavigateCoursePage = async (
  courseId: string,
  pageIndex: number,
  props: CourseHandlersProps
) => {
  const {
    apiConfig,
    sessionIds,
    addMessage,
    setIsLoading,
    setCurrentCoursePage,
    setCurrentCourse,
    setCourseQuiz,
    setCourseQuizAnswers
  } = props;

  try {
    setIsLoading(true);
    
    // Navigate to the page
    const result = await navigateCoursePage(apiConfig, courseId, pageIndex);
    
    if (result.success) {
      // Set current page or quiz
      if (result.data && result.data.current_page) {
        const pageData = result.data.current_page;
        if (pageData.page_type === 'quiz' && pageData.quiz_data) {
          // Quiz page: initialize course quiz state
          const quizQuestions = Array.isArray(pageData.quiz_data)
            ? pageData.quiz_data.map(normalizeQuizQuestion)
            : [normalizeQuizQuestion(pageData.quiz_data)];
          const courseQuizState = {
            questions: quizQuestions,
            currentQuestion: 0,
            score: 0,
            attempts: 0,
            pageIndex: pageData.page_index,
            totalPages: pageData.total_pages || 1
          };
          setCurrentCoursePage(null);
          setCourseQuiz(courseQuizState);
          setCourseQuizAnswers(initializeCourseQuizAnswers(quizQuestions.length));
          
          // Course start message removed per user request
        } else {
          // Content page
          const page: CoursePage = {
            id: pageData.id,
            title: pageData.title,
            content: pageData.content,
            pageNumber: pageData.page_index + 1,
            totalPages: pageData.total_pages || 1,
            pageType: pageData.page_type,
            quizData: pageData.quiz_data
          };
          setCurrentCoursePage(page);
          
          // Course start message removed per user request
        }
      }
    } else {
      throw new Error(result.message || 'Failed to navigate course page');
    }
    
  } catch (error) {
    let errorMsg = 'Sorry, there was an error navigating the course. Please try again.';
    
    // Check for specific error messages
    if (error instanceof Error) {
      if (error.message.includes('Course not found')) {
        errorMsg = 'The requested course could not be found. It may still be being prepared. Please try again in a moment.';
      } else if (error.message.includes('Page') && error.message.includes('not found')) {
        errorMsg = 'The requested page could not be found. The course content may still be being prepared. Please try again in a moment.';
      } else if (error.message.includes('properly registered')) {
        errorMsg = 'The course is still being set up. Please wait a moment and try again.';
      }
    }
    
    const errorMessage = createSystemMessage(
      errorMsg,
      sessionIds.sessionId,
      sessionIds.userId
    );
    addMessage(errorMessage);
  } finally {
    setIsLoading(false);
  }
};

export const handleSubmitCourseQuiz = async (
  courseId: string,
  pageIndex: number,
  selectedOption: string,
  correct: boolean,
  props: CourseHandlersProps,
  currentTotalPages?: number  // Add optional parameter to preserve total pages
) => {
  const {
    apiConfig,
    sessionIds,
    addMessage,
    setIsLoading,
    setCurrentCoursePage,
    setCourseQuiz,
    setCourseQuizAnswers
  } = props;

  try {
    setIsLoading(true);
    
    // Submit quiz answer
    const result = await submitCourseQuiz(apiConfig, courseId, pageIndex, selectedOption, correct);
    
    if (result.success) {
      // Clear quiz state first
      setCourseQuiz(null);
      setCourseQuizAnswers(initializeCourseQuizAnswers(0));
      
      // Feedback message removed - quiz component shows its own summary now
      
      // Navigate to next page if available
      if (result.next_page) {
        const pageData = result.next_page;
        // Use currentTotalPages as fallback if backend doesn't return correct total_pages
        const totalPages = pageData.total_pages || currentTotalPages || 1;
        
        if (pageData.page_type === 'quiz' && pageData.quiz_data) {
          // Next page is also a quiz
          const quizQuestions = Array.isArray(pageData.quiz_data)
            ? pageData.quiz_data.map(normalizeQuizQuestion)
            : [normalizeQuizQuestion(pageData.quiz_data)];
          const courseQuizState = {
            questions: quizQuestions,
            currentQuestion: 0,
            score: 0,
            attempts: 0,
            pageIndex: pageData.page_index,
            totalPages: totalPages
          };
    setCurrentCoursePage(null);
          setCourseQuiz(courseQuizState);
          setCourseQuizAnswers(initializeCourseQuizAnswers(quizQuestions.length));
          
          // Course start message removed per user request
        } else {
          // Next page is content
          const page: CoursePage = {
            id: pageData.id,
            title: pageData.title,
            content: pageData.content,
            pageNumber: pageData.page_index + 1,
            totalPages: totalPages,
            pageType: pageData.page_type,
            quizData: pageData.quiz_data
          };
          setCurrentCoursePage(page);
          
          // Course start message removed per user request
        }
      } else {
        // No next page - course might be complete
        const completionMessage = createSystemMessage(
          `🎉 **Quiz completed!** You've reached the end of this course section.`,
          sessionIds.sessionId,
          sessionIds.userId
        );
        addMessage(completionMessage);
      }
    } else {
      throw new Error(result.message || 'Failed to submit quiz answer');
    }
    
  } catch (error) {
    const errorMessage = createSystemMessage(
      'Sorry, there was an error submitting your answer. Please try again.',
      sessionIds.sessionId,
      sessionIds.userId
    );
    addMessage(errorMessage);
  } finally {
    setIsLoading(false);
  }
};

export const handleCompleteCourse = async (
  courseId: string,
  props: CourseHandlersProps
) => {
  const {
    apiConfig,
    sessionIds,
    addMessage,
    setIsLoading,
    setCourseCompleting,
    closeCurrentDisplays
  } = props;

  try {
    setIsLoading(true);
    
    // Show shimmer loading for course completion
    if (setCourseCompleting) {
      setCourseCompleting(true);
    }
    
    // Complete the course
    const result = await completeCourse(apiConfig, courseId);
    
    if (result.success) {
      closeCurrentDisplays();
      
      // Extract course title and score
      const courseTitle = result.data?.completion_summary?.course_title || result.data?.course_title || 'the course';
      const score = result.data?.completion_summary?.score;
      
      // Show green congratulations message
      const completionMessage = createSystemMessage(
        `🎉 **Congratulations! Course Completed!** 🎉

${courseTitle ? `**Course:** ${courseTitle}` : ''}
${score ? `**Final Score:** ${score}%` : ''}

You've successfully completed the course! 🚀

Keep up the great work and continue learning! 💪`,
        sessionIds.sessionId,
        sessionIds.userId
      );
      
      // Add congratulations class to the message
      completionMessage.metadata = { ...completionMessage.metadata, isCongratulations: true };
      addMessage(completionMessage);
      
      // Show courses list after a short delay
      setTimeout(() => {
        // Trigger the courses list to be shown
        if (props.setShowCourseList) {
          props.setShowCourseList(true);
        }
      }, 2000);
    } else {
      throw new Error(result.message || 'Failed to complete course');
    }
    
  } catch (error) {
    const errorMessage = createSystemMessage(
      'Sorry, there was an error completing the course. Please try again.',
      sessionIds.sessionId,
      sessionIds.userId
    );
    addMessage(errorMessage);
  } finally {
    setIsLoading(false);
    if (setCourseCompleting) {
      setCourseCompleting(false);
    }
  }
}; 