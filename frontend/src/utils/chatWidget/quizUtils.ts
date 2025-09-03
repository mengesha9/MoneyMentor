import { QuizQuestion, Course } from '../../types';

export interface QuizFeedback {
  correct: boolean;
  explanation: string;
}

export interface CourseQuizState {
  questions: QuizQuestion[];
  currentQuestion: number;
  score: number;
  attempts: number;
  pageIndex: number; // Track which page this quiz belongs to
  totalPages: number; // Track total pages in the course
}

export interface CourseQuizAnswers {
  answers: number[];
  currentQuestionIndex: number;
}

/**
 * Initialize course quiz state
 */
export const initializeCourseQuiz = (course: Course, pageIndex: number = 0): CourseQuizState => ({
  questions: course.quizQuestions,
  currentQuestion: 0,
  score: 0,
  attempts: 1,
  pageIndex: pageIndex,
  totalPages: course.quizQuestions.length
});

/**
 * Initialize course quiz answers
 */
export const initializeCourseQuizAnswers = (questionCount: number): CourseQuizAnswers => ({
  answers: new Array(questionCount).fill(-1),
  currentQuestionIndex: 0
});

/**
 * Handle course quiz answer selection
 */
export const handleCourseQuizAnswer = (
  state: CourseQuizAnswers,
  questionIndex: number,
  selectedOption: number
): CourseQuizAnswers => {
  const newAnswers = [...state.answers];
  newAnswers[questionIndex] = selectedOption;
  
  return {
    ...state,
    answers: newAnswers
  };
};

/**
 * Navigate to next quiz question
 */
export const navigateToNextQuizQuestion = (
  state: CourseQuizAnswers,
  maxQuestions: number
): CourseQuizAnswers => {
  if (state.currentQuestionIndex >= maxQuestions - 1) {
    return state;
  }
  
  return {
    ...state,
    currentQuestionIndex: state.currentQuestionIndex + 1
  };
};

/**
 * Navigate to previous quiz question
 */
export const navigateToPreviousQuizQuestion = (
  state: CourseQuizAnswers
): CourseQuizAnswers => {
  if (state.currentQuestionIndex <= 0) {
    return state;
  }
  
  return {
    ...state,
    currentQuestionIndex: state.currentQuestionIndex - 1
  };
};

/**
 * Navigate to specific quiz question
 */
export const navigateToQuizQuestion = (
  state: CourseQuizAnswers,
  questionIndex: number,
  maxQuestions: number
): CourseQuizAnswers => {
  if (questionIndex < 0 || questionIndex >= maxQuestions) {
    return state;
  }
  
  return {
    ...state,
    currentQuestionIndex: questionIndex
  };
};

/**
 * Check if all quiz questions are answered
 */
export const areAllQuestionsAnswered = (answers: number[]): boolean => {
  return !answers.some(answer => answer === -1);
};

/**
 * Calculate quiz score
 */
export const calculateQuizScore = (
  answers: number[],
  questions: QuizQuestion[]
): number => {
  let correctAnswers = 0;
  
  answers.forEach((answer, index) => {
    if (answer === questions[index].correctAnswer) {
      correctAnswers++;
    }
  });
  
  return Math.round((correctAnswers / questions.length) * 100);
};

/**
 * Create quiz feedback
 */
export const createQuizFeedback = (
  selectedOption: number,
  correctAnswer: number,
  explanation: string
): QuizFeedback => ({
  correct: selectedOption === correctAnswer,
  explanation
});

/**
 * Format quiz result message
 */
export const formatQuizResultMessage = (
  score: number,
  passed: boolean,
  explanations?: string[]
): string => {
  let resultMessage = `🎯 **Quiz Results: ${score}%**\n\n`;
  
  if (passed) {
    resultMessage += '🎉 **Congratulations!** You passed the course!\n\n';
    resultMessage += 'You can now move on to the next course or continue chatting for personalized advice.';
  } else {
    resultMessage += '📚 **Let\'s review the material**\n\n';
    if (explanations) {
      explanations.forEach((explanation: string, index: number) => {
        resultMessage += `**Question ${index + 1}:** ${explanation}\n\n`;
      });
    }
    resultMessage += 'Feel free to retake the course or ask me any questions!';
  }
  
  return resultMessage;
};

/**
 * Reset course quiz state
 */
export const resetCourseQuizState = (): {
  quiz: CourseQuizState | null;
  answers: CourseQuizAnswers;
} => ({
  quiz: null,
  answers: {
    answers: [],
    currentQuestionIndex: 0
  }
});

/**
 * Get quiz progress percentage
 */
export const getQuizProgress = (
  currentQuestion: number,
  totalQuestions: number
): number => {
  return Math.round(((currentQuestion + 1) / totalQuestions) * 100);
};

/**
 * Check if quiz question is answered
 */
export const isQuestionAnswered = (
  answers: number[],
  questionIndex: number
): boolean => {
  return answers[questionIndex] !== -1;
};

/**
 * Get answered questions count
 */
export const getAnsweredQuestionsCount = (answers: number[]): number => {
  return answers.filter(answer => answer !== -1).length;
}; 