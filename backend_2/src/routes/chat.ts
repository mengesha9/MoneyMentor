import { Router } from 'express';
import { ChatController } from '../controllers';
import { asyncHandler } from '../middleware/errorHandler';

const router = Router();
const chatController = new ChatController();

// Test route to verify router is working
router.get('/test', chatController.test.bind(chatController));

// Test Google Sheets connectivity
router.get('/test-sheets', asyncHandler(chatController.testSheets.bind(chatController)));

// GET /api/chat/courses - Get available courses
router.get('/courses', asyncHandler(chatController.getCourses.bind(chatController)));

// POST /api/chat/course/start - Start a course
router.post('/course/start', asyncHandler(chatController.startCourse.bind(chatController)));

// POST /api/chat/course/navigate - Navigate to course page
router.post('/course/navigate', asyncHandler(chatController.navigateCourse.bind(chatController)));

// POST /api/chat/course/quiz - Submit course quiz
router.post('/course/quiz', asyncHandler(chatController.submitCourseQuiz.bind(chatController)));

// GET /api/chat/diagnostic - Get diagnostic quiz questions
router.get('/diagnostic', asyncHandler(chatController.getDiagnostic.bind(chatController)));

// POST /api/chat - Main chat endpoint
router.post('/', asyncHandler(chatController.chat.bind(chatController)));

export { router as chatRouter }; 