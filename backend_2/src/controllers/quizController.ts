import { Request, Response } from 'express';
import { 
  QuizLogRequest, 
  QuizLogResponse,
  validateQuizResponse 
} from '../types';
import { QuizService } from '../services/quizService';
import { CourseService } from '../services/courseService';
import { GoogleSheetsService } from '../services/googleSheetsService';
import { logger } from '../utils/logger';

export class QuizController {
  private quizService: QuizService;
  private courseService: CourseService;
  private googleSheetsService: GoogleSheetsService;

  constructor() {
    this.quizService = new QuizService();
    this.courseService = new CourseService();
    this.googleSheetsService = new GoogleSheetsService();
  }

  // POST /api/quiz/log - Log quiz response
  async logQuizResponse(req: Request, res: Response): Promise<void> {
    const quizResponse: QuizLogRequest = req.body;

    // Validation
    if (!validateQuizResponse(quizResponse)) {
      res.status(400).json({
        success: false,
        error: 'Invalid quiz response data'
      });
      return;
    }

    try {
      // Log to internal service
      await this.quizService.logQuizResponse(quizResponse);

      // Log to Google Sheets
      await this.googleSheetsService.logQuizResponse(quizResponse);

      // TODO: Log to database if configured

      const response: QuizLogResponse = {
        success: true,
        data: {
          logged: true,
          timestamp: new Date().toISOString(),
          logId: `quiz_${Date.now()}_${quizResponse.userId}`
        }
      };

      logger.info('Quiz response logged successfully', {
        userId: quizResponse.userId,
        quizId: quizResponse.quizId,
        correct: quizResponse.correct
      });

      res.json(response);

    } catch (error) {
      logger.error('Quiz logging error:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to log quiz response'
      });
    }
  }

  // GET /api/quiz/diagnostic - Get diagnostic test
  async getDiagnosticTest(req: Request, res: Response): Promise<void> {
    try {
      const diagnosticTest = await this.quizService.getDiagnosticTest();
      
      res.json({
        success: true,
        data: diagnosticTest
      });

    } catch (error) {
      logger.error('Diagnostic test retrieval error:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to retrieve diagnostic test'
      });
    }
  }

  // GET /api/quiz/diagnostic/question/:index - Get specific diagnostic question
  async getDiagnosticQuestion(req: Request, res: Response): Promise<void> {
    const { index } = req.params;
    const questionIndex = parseInt(index);

    if (isNaN(questionIndex) || questionIndex < 0) {
      res.status(400).json({
        success: false,
        error: 'Invalid question index'
      });
      return;
    }

    try {
      const diagnosticTest = await this.quizService.getDiagnosticTest();
      
      if (questionIndex >= diagnosticTest.questions.length) {
        res.status(404).json({
          success: false,
          error: 'Question not found'
        });
        return;
      }

      const question = diagnosticTest.questions[questionIndex];
      
      res.json({
        success: true,
        data: {
          question,
          currentIndex: questionIndex,
          totalQuestions: diagnosticTest.totalQuestions,
          isLastQuestion: questionIndex === diagnosticTest.questions.length - 1
        }
      });

    } catch (error) {
      logger.error('Diagnostic question retrieval error:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to retrieve diagnostic question'
      });
    }
  }

  // POST /api/quiz/start-diagnostic - Start diagnostic test and get first question
  async startDiagnosticTest(req: Request, res: Response): Promise<void> {
    const { userId, sessionId } = req.body;

    if (!userId || !sessionId) {
      res.status(400).json({
        success: false,
        error: 'Missing userId or sessionId'
      });
      return;
    }

    try {
      const diagnosticTest = await this.quizService.getDiagnosticTest();
      
      if (diagnosticTest.questions.length === 0) {
        res.status(404).json({
          success: false,
          error: 'No diagnostic questions available'
        });
        return;
      }

      const firstQuestion = diagnosticTest.questions[0];
      
      res.json({
        success: true,
        data: {
          question: firstQuestion,
          currentIndex: 0,
          totalQuestions: diagnosticTest.totalQuestions,
          isLastQuestion: diagnosticTest.questions.length === 1,
          message: '🎯 **Starting Diagnostic Test**\n\nThis quick assessment will help me understand your financial knowledge level and provide personalized course recommendations.\n\n📊 **3 questions** covering budgeting, saving, investing, and debt management\n⏱️ **Takes about 1-2 minutes**\n\nLet\'s begin!'
        }
      });

    } catch (error) {
      logger.error('Start diagnostic error:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to start diagnostic test'
      });
    }
  }

  // GET /api/quiz/micro/:topic - Get micro quiz for topic
  async getMicroQuiz(req: Request, res: Response): Promise<void> {
    const { topic } = req.params;

    if (!topic || typeof topic !== 'string') {
      res.status(400).json({
        success: false,
        error: 'Invalid topic parameter'
      });
      return;
    }

    try {
      const microQuiz = await this.quizService.getMicroQuiz(topic);
      
      res.json({
        success: true,
        data: microQuiz
      });

    } catch (error) {
      logger.error('Micro quiz retrieval error:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to retrieve micro quiz'
      });
    }
  }

  // POST /api/quiz/session - Create or update quiz session
  async createOrUpdateSession(req: Request, res: Response): Promise<void> {
    const { userId, sessionId } = req.body;

    if (!userId || typeof userId !== 'string') {
      res.status(400).json({
        success: false,
        error: 'Invalid user ID'
      });
      return;
    }

    try {
      const session = await this.quizService.getOrCreateSession(userId, sessionId);
      
      res.json({
        success: true,
        data: session
      });

    } catch (error) {
      logger.error('Session creation error:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to create session'
      });
    }
  }

  // POST /api/quiz/complete-diagnostic - Mark diagnostic test as completed
  async completeDiagnosticTest(req: Request, res: Response): Promise<void> {
    const { userId, sessionId, score } = req.body;

    if (!userId || !sessionId) {
      res.status(400).json({
        success: false,
        error: 'Missing userId or sessionId'
      });
      return;
    }

    try {
      await this.quizService.updateSession(sessionId, { 
        completedPreTest: true,
        confidenceRating: score || 0
      });

      // Get recommended courses based on diagnostic score
      const recommendedCourses = await this.courseService.getRecommendedCourses(score || 0);
      
      res.json({
        success: true,
        data: {
          completed: true,
          message: 'Diagnostic test completed successfully',
          score: score || 0,
          recommendedCourses
        }
      });

    } catch (error) {
      logger.error('Diagnostic completion error:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to complete diagnostic test'
      });
    }
  }

  // GET /api/quiz/debug/:sessionId - Debug endpoint to check session state
  async debugSession(req: Request, res: Response): Promise<void> {
    const { sessionId } = req.params;

    try {
      const session = await this.quizService.getOrCreateSession('debug-user', sessionId);
      const shouldInject = await this.quizService.shouldInjectQuiz(sessionId);
      
      res.json({
        success: true,
        data: {
          session,
          shouldInjectQuiz: shouldInject,
          nextQuizAt: session.messageCount + (2 - (session.messageCount % 2))
        }
      });

    } catch (error) {
      logger.error('Debug endpoint error:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to get debug info'
      });
    }
  }

  // POST /api/quiz/skip-diagnostic - Skip diagnostic test for testing
  async skipDiagnosticTest(req: Request, res: Response): Promise<void> {
    const { userId, sessionId } = req.body;

    if (!userId || !sessionId) {
      res.status(400).json({
        success: false,
        error: 'Missing userId or sessionId'
      });
      return;
    }

    try {
      await this.quizService.updateSession(sessionId, { 
        completedPreTest: true,
        confidenceRating: 100 // Mark as completed with high score
      });
      
      res.json({
        success: true,
        data: {
          skipped: true,
          message: 'Diagnostic test skipped for testing'
        }
      });

    } catch (error) {
      logger.error('Skip diagnostic error:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to skip diagnostic test'
      });
    }
  }
} 