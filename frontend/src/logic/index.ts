// Export existing handlers
export * from './messageHandlers';
export * from './diagnosticHandlers';
export * from './courseHandlers';
export * from './quizHandlers';
export * from './fileHandlers';

// Export new handlers
export * from './sidebarHandlers';
export * from './profileHandlers';

// Message handlers
export { handleSendMessage } from './messageHandlers';
export type { MessageHandlersProps } from './messageHandlers';

// Diagnostic handlers
export { 
  handleStartDiagnosticTest, 
  handleDiagnosticQuizAnswer, 
  handleNextDiagnosticQuestion,
  handleCompleteDiagnosticTest
} from './diagnosticHandlers';
export type { DiagnosticHandlersProps } from './diagnosticHandlers';

// Course handlers
export { 
  handleCoursesList,
  handleStartCourse,
  handleNavigateCoursePage,
  handleCompleteCourse,
  handleSubmitCourseQuiz
} from './courseHandlers';
export type { CourseHandlersProps } from './courseHandlers';

// Quiz handlers
export { handleQuizAnswer } from './quizHandlers';
export type { QuizHandlersProps } from './quizHandlers';

// File handlers
export { handleFileUpload, handleRemoveFile } from './fileHandlers';
export type { FileHandlersProps } from './fileHandlers'; 