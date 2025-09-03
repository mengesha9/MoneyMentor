import { Router } from 'express';
import { QuizController } from '../controllers';
import { asyncHandler } from '../middleware/errorHandler';

const router = Router();
const quizController = new QuizController();

// POST /api/quiz/log - Log quiz response
router.post('/log', asyncHandler(quizController.logQuizResponse.bind(quizController)));

// GET /api/quiz/diagnostic - Get diagnostic test
router.get('/diagnostic', asyncHandler(quizController.getDiagnosticTest.bind(quizController)));

// GET /api/quiz/diagnostic/question/:index - Get specific diagnostic question
router.get('/diagnostic/question/:index', asyncHandler(quizController.getDiagnosticQuestion.bind(quizController)));

// POST /api/quiz/start-diagnostic - Start diagnostic test and get first question
router.post('/start-diagnostic', asyncHandler(quizController.startDiagnosticTest.bind(quizController)));

// GET /api/quiz/micro/:topic - Get micro quiz for topic
router.get('/micro/:topic', asyncHandler(quizController.getMicroQuiz.bind(quizController)));

// POST /api/quiz/session - Create or update quiz session
router.post('/session', asyncHandler(quizController.createOrUpdateSession.bind(quizController)));

// POST /api/quiz/complete-diagnostic - Mark diagnostic test as completed
router.post('/complete-diagnostic', asyncHandler(quizController.completeDiagnosticTest.bind(quizController)));

// GET /api/quiz/debug/:sessionId - Debug endpoint to check session state
router.get('/debug/:sessionId', asyncHandler(quizController.debugSession.bind(quizController)));

// POST /api/quiz/skip-diagnostic - Skip diagnostic test for testing
router.post('/skip-diagnostic', asyncHandler(quizController.skipDiagnosticTest.bind(quizController)));

export { router as quizRouter }; 