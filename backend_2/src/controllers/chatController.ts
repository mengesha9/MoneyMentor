import { Request, Response } from 'express';
import { v4 as uuidv4 } from 'uuid';
import { 
  ChatApiRequest, 
  ChatApiResponse, 
  validateUserId, 
  validateMessage,
  CalculationInput,
  CALC_DEFAULTS
} from '../types';
import { QuizService } from '../services/quizService';
import { CalcService } from '../services/calcService';
import { CourseService } from '../services/courseService';
import { GoogleSheetsService } from '../services/googleSheetsService';
import { logger } from '../utils/logger';
import { getUserContent } from '../routes/content';

export class ChatController {
  private quizService: QuizService;
  private calcService: CalcService;
  private courseService: CourseService;
  private googleSheetsService: GoogleSheetsService;

  constructor() {
    this.quizService = new QuizService();
    this.calcService = new CalcService();
    this.courseService = new CourseService();
    this.googleSheetsService = new GoogleSheetsService();
  }

  // Test route to verify controller is working
  async test(req: Request, res: Response): Promise<void> {
    res.json({ message: 'Chat controller is working!' });
  }

  // Test Google Sheets connectivity
  async testSheets(req: Request, res: Response): Promise<void> {
    try {
      const status = this.googleSheetsService.getStatus();
      const connectionTest = await this.googleSheetsService.testConnection();
      
      res.json({
        success: true,
        data: {
          enabled: status.enabled,
          spreadsheetId: status.spreadsheetId,
          connectionWorking: connectionTest,
          message: connectionTest ? 'Google Sheets is working!' : 'Google Sheets connection failed'
        }
      });
    } catch (error) {
      logger.error('Google Sheets test error:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to test Google Sheets connection'
      });
    }
  }

  // GET /api/chat/courses - Get available courses
  async getCourses(req: Request, res: Response): Promise<void> {
    const { userId } = req.query;
    
    if (!userId || !validateUserId(userId as string)) {
      res.status(400).json({
        success: false,
        error: 'Invalid user ID'
      });
      return;
    }

    try {
      const courses = await this.courseService.getCoursesForUser(userId as string);
      res.json({
        success: true,
        data: courses
      });
    } catch (error) {
      logger.error('Error fetching courses:', error);
      res.status(500).json({
        success: false,
        error: 'Internal server error'
      });
    }
  }

  // POST /api/chat/course/start - Start a course
  async startCourse(req: Request, res: Response): Promise<void> {
    const { userId, sessionId, courseId } = req.body;
    
    if (!validateUserId(userId) || !courseId) {
      res.status(400).json({
        success: false,
        error: 'Invalid parameters'
      });
      return;
    }

    try {
      const session = await this.quizService.getOrCreateSession(userId, sessionId);
      const courseSession = await this.courseService.startCourse(userId, session.sessionId, courseId);
      
      if (!courseSession) {
        res.status(404).json({
          success: false,
          error: 'Course not found'
        });
        return;
      }

      res.json({
        success: true,
        data: {
          courseSession,
          currentPage: courseSession.activeCourse?.pages[0]
        }
      });
    } catch (error) {
      logger.error('Error starting course:', error);
      res.status(500).json({
        success: false,
        error: 'Internal server error'
      });
    }
  }

  // POST /api/chat/course/navigate - Navigate to course page
  async navigateCourse(req: Request, res: Response): Promise<void> {
    const { sessionId, pageIndex } = req.body;
    
    if (!sessionId || typeof pageIndex !== 'number') {
      res.status(400).json({
        success: false,
        error: 'Invalid parameters'
      });
      return;
    }

    try {
      const page = await this.courseService.navigateToPage(sessionId, pageIndex);
      
      if (!page) {
        res.status(404).json({
          success: false,
          error: 'Page not found'
        });
        return;
      }

      // Log course progress to Google Sheets
      try {
        await this.googleSheetsService.logCourseProgress({
          userId: 'unknown',
          sessionId: sessionId,
          courseId: 'current_course',
          courseName: 'Current Course',
          pageNumber: pageIndex + 1,
          totalPages: page.totalPages || 0,
          completed: false,
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        logger.error('Failed to log course progress to Google Sheets:', error);
      }

      res.json({
        success: true,
        data: { page }
      });
    } catch (error) {
      logger.error('Error navigating course:', error);
      res.status(500).json({
        success: false,
        error: 'Internal server error'
      });
    }
  }

  // POST /api/chat/course/quiz - Submit course quiz
  async submitCourseQuiz(req: Request, res: Response): Promise<void> {
    const { sessionId, answers } = req.body;
    
    if (!sessionId || !Array.isArray(answers)) {
      res.status(400).json({
        success: false,
        error: 'Invalid parameters'
      });
      return;
    }

    try {
      const result = await this.courseService.submitCourseQuiz(sessionId, answers);
      res.json({
        success: true,
        data: result
      });
    } catch (error) {
      logger.error('Error submitting course quiz:', error);
      res.status(500).json({
        success: false,
        error: 'Internal server error'
      });
    }
  }

  // GET /api/chat/diagnostic - Get diagnostic quiz questions
  async getDiagnostic(req: Request, res: Response): Promise<void> {
    try {
      const questions = await this.courseService.getRandomDiagnosticQuestions();
      res.json({
        success: true,
        data: questions
      });
    } catch (error) {
      logger.error('Error fetching diagnostic questions:', error);
      res.status(500).json({
        success: false,
        error: 'Internal server error'
      });
    }
  }

  // POST /api/chat - Main chat endpoint
  async chat(req: Request, res: Response): Promise<void> {
    const chatRequest: ChatApiRequest = req.body;

    // Validation
    if (!validateUserId(chatRequest.userId)) {
      res.status(400).json({
        success: false,
        error: 'Invalid user ID'
      });
      return;
    }

    if (!validateMessage(chatRequest.message)) {
      res.status(400).json({
        success: false,
        error: 'Invalid message'
      });
      return;
    }

    try {
      // Get or create quiz session
      const session = await this.quizService.getOrCreateSession(chatRequest.userId, chatRequest.sessionId);
      
      // Increment message count for quiz injection logic
      await this.quizService.incrementMessageCount(session.sessionId);

      // Log chat message to Google Sheets
      try {
        await this.googleSheetsService.logChatMessage({
          userId: chatRequest.userId,
          sessionId: session.sessionId,
          message: chatRequest.message,
          response: '', // Empty response for user messages
          timestamp: new Date().toISOString(),
          messageType: 'user'
        });
      } catch (error) {
        logger.error('Failed to log chat message to Google Sheets:', error);
      }

      // Check for calculation requests
      const calculationInput = this.detectCalculationRequest(chatRequest.message);
      if (calculationInput) {
        const result = await this.calcService.calculate(calculationInput);
        const responseText = this.formatCalculationResponse(result);
        
        const response: ChatApiResponse = {
          success: true,
          data: {
            responseText,
            sessionId: session.sessionId,
            messageId: uuidv4(),
            calculationResult: result
          }
        };

        res.json(response);
        return;
      }

      // Handle special commands
      if (chatRequest.message.toLowerCase().includes('/courses')) {
        const courses = await this.courseService.getCoursesForUser(chatRequest.userId);
        const responseText = this.generateCourseListResponse(courses);
        
        const response: ChatApiResponse = {
          success: true,
          data: {
            responseText,
            sessionId: session.sessionId,
            messageId: uuidv4(),
            courseList: courses
          }
        };

        res.json(response);
        return;
      }

      if (chatRequest.message.toLowerCase().includes('/chat')) {
        const responseText = this.generateChatModeResponse();
        
        const response: ChatApiResponse = {
          success: true,
          data: {
            responseText,
            sessionId: session.sessionId,
            messageId: uuidv4()
          }
        };

        res.json(response);
        return;
      }

      // Check if we should inject a quiz
      const shouldInjectQuiz = await this.quizService.shouldInjectQuiz(session.sessionId);
      let quizQuestion = null;

      if (shouldInjectQuiz && session.completedPreTest) {
        quizQuestion = await this.quizService.generateContextualQuiz([chatRequest.message]);
        
        if (!quizQuestion) {
          const topics = ['budgeting', 'savings', 'investing', 'debt_management', 'emergency_fund'];
          const randomTopic = topics[Math.floor(Math.random() * topics.length)];
          quizQuestion = await this.quizService.getMicroQuiz(randomTopic);
        }
      }

      // Get user's uploaded content for context
      const userContent = getUserContent(chatRequest.userId, session.sessionId);
      
      // Generate response based on message content and user context
      let responseText: string;
      if (userContent.length > 0) {
        responseText = this.generateResponseWithUserContent(chatRequest.message, userContent.join('\n\n'));
      } else {
        responseText = this.generateContextualResponse(chatRequest.message, userContent);
      }

      const response: ChatApiResponse = {
        success: true,
        data: {
          responseText,
          sessionId: session.sessionId,
          messageId: uuidv4(),
          quizQuestion: quizQuestion || undefined
        }
      };

      logger.info('Chat response generated', {
        userId: chatRequest.userId,
        sessionId: session.sessionId,
        hasQuiz: !!quizQuestion,
        messageLength: chatRequest.message.length,
        responseLength: responseText.length
      });

      res.json(response);

    } catch (error) {
      logger.error('Chat processing error:', error);
      res.status(500).json({
        success: false,
        error: 'Internal server error'
      });
    }
  }

  // Helper methods
  private detectCalculationRequest(message: string): CalculationInput | null {
    const lowerMessage = message.toLowerCase();
    
    // Credit Card Payoff Detection
    if (lowerMessage.includes('credit card') || lowerMessage.includes('payoff') || 
        lowerMessage.includes('debt') || lowerMessage.includes('pay off')) {
      const balance = this.extractNumber(message, ['balance', 'owe', 'debt', 'amount']);
      const interestRate = this.extractNumber(message, ['interest', 'rate', 'apr', '%']);
      const monthlyPayment = this.extractNumber(message, ['payment', 'monthly', 'pay']);
      
      if (balance || interestRate || monthlyPayment) {
        return {
          type: 'credit_card_payoff',
          inputs: {
            principal: balance || 1000,
            interestRate: interestRate || CALC_DEFAULTS.DEFAULT_CREDIT_CARD_APR,
            monthlyPayment: monthlyPayment || 0
          }
        };
      }
    }

    // Savings Goal Detection
    if (lowerMessage.includes('save') || lowerMessage.includes('saving') || 
        lowerMessage.includes('goal') || lowerMessage.includes('target')) {
      const targetAmount = this.extractNumber(message, ['save', 'goal', 'target', 'need', 'want']);
      const timeframe = this.extractNumber(message, ['month', 'year', 'time']);
      const currentSavings = this.extractNumber(message, ['have', 'current', 'already', 'saved']);
      const interestRate = this.extractNumber(message, ['interest', 'rate', 'return', '%']);
      
      if (targetAmount || timeframe) {
        return {
          type: 'savings_goal',
          inputs: {
            targetAmount: targetAmount || 10000,
            timeframe: timeframe || 12,
            currentSavings: currentSavings || 0,
            interestRate: interestRate || CALC_DEFAULTS.DEFAULT_SAVINGS_RATE
          }
        };
      }
    }

    // Loan Amortization Detection
    if (lowerMessage.includes('loan') || lowerMessage.includes('mortgage') || 
        lowerMessage.includes('borrow') || lowerMessage.includes('finance')) {
      const principal = this.extractNumber(message, ['loan', 'borrow', 'amount', 'principal']);
      const interestRate = this.extractNumber(message, ['interest', 'rate', 'apr', '%']);
      const timeframe = this.extractNumber(message, ['year', 'month', 'term']);
      
      if (principal || interestRate) {
        return {
          type: 'loan_amortization',
          inputs: {
            principal: principal || 100000,
            interestRate: interestRate || 5.0,
            timeframe: timeframe ? (timeframe > 100 ? timeframe : timeframe * 12) : 360 // Convert years to months if needed
          }
        };
      }
    }

    return null;
  }

  private extractNumber(text: string, keywords: string[]): number | null {
    for (const keyword of keywords) {
      // Try multiple patterns for each keyword
      const patterns = [
        // Pattern 1: keyword followed by currency/number (e.g., "balance $5000", "rate 18%")
        new RegExp(`${keyword}[^\\d]*\\$?([\\d,]+(?:\\.\\d{1,2})?)%?`, 'i'),
        // Pattern 2: currency/number followed by keyword (e.g., "$5000 balance", "18% rate")
        new RegExp(`\\$?([\\d,]+(?:\\.\\d{1,2})?)%?[^\\d]*${keyword}`, 'i'),
        // Pattern 3: keyword with "of" or "is" (e.g., "balance of $5000", "rate is 18%")
        new RegExp(`${keyword}\\s+(?:of|is)\\s+\\$?([\\d,]+(?:\\.\\d{1,2})?)%?`, 'i')
      ];
      
      for (const regex of patterns) {
        const match = text.match(regex);
        if (match) {
          const numberStr = match[1].replace(/,/g, '');
          const number = parseFloat(numberStr);
          if (!isNaN(number) && number > 0) {
            return number;
          }
        }
      }
    }
    
    // Fallback: look for standalone numbers near keywords
    for (const keyword of keywords) {
      const words = text.toLowerCase().split(/\s+/);
      const keywordIndex = words.findIndex(word => word.includes(keyword));
      if (keywordIndex !== -1) {
        // Check words around the keyword
        for (let i = Math.max(0, keywordIndex - 2); i <= Math.min(words.length - 1, keywordIndex + 2); i++) {
          const word = words[i].replace(/[^\d.,]/g, '');
          if (word) {
            const number = parseFloat(word.replace(/,/g, ''));
            if (!isNaN(number) && number > 0) {
              return number;
            }
          }
        }
      }
    }
    
    return null;
  }

  private formatCalculationResponse(result: any): string {
    if (!result || !result.type) {
      return "I couldn't process that calculation. Please provide more specific details.";
    }

    switch (result.type) {
      case 'credit_card_payoff':
        return `💳 **Credit Card Payoff Plan**\n\n⏰ **Payoff Time**: ${result.monthsToPayoff} months\n💵 **Monthly Payment**: $${result.monthlyPayment?.toFixed(2)}\n💰 **Total Interest**: $${result.totalInterest?.toFixed(2)}\n📊 **Total Paid**: $${result.totalAmount?.toFixed(2)}\n\n${result.stepByStepPlan?.slice(0, 3).join('\n') || ''}\n\n💡 **Tip**: Pay extra toward principal to save on interest!`;
      
      case 'savings_goal':
        return `💰 **Savings Goal Plan**\n\n🎯 **Target Amount**: $${result.totalAmount?.toFixed(2)}\n💵 **Monthly Savings Needed**: $${result.monthlyPayment?.toFixed(2)}\n📅 **Time to Goal**: ${result.monthsToPayoff} months\n📈 **Interest Earned**: $${result.totalInterest?.toFixed(2)}\n\n${result.stepByStepPlan?.slice(0, 3).join('\n') || ''}\n\n🚀 **Tip**: Automate your savings to stay consistent!`;
      
      case 'loan_amortization':
        return `🏠 **Loan Payment Plan**\n\n💵 **Monthly Payment**: $${result.monthlyPayment?.toFixed(2)}\n📅 **Loan Term**: ${Math.round(result.monthsToPayoff / 12)} years\n💰 **Total Interest**: $${result.totalInterest?.toFixed(2)}\n📊 **Total Paid**: $${result.totalAmount?.toFixed(2)}\n\n${result.stepByStepPlan?.slice(0, 3).join('\n') || ''}\n\n💡 **Tip**: Extra principal payments can save thousands!`;
      
      default:
        return "I've processed your calculation, but couldn't format the results properly.";
    }
  }

  private generateContextualResponse(message: string, userContent: string[]): string {
    return "I'm here to help with financial questions! I can assist with budgeting, investing, debt management, and more. What specific topic interests you?";
  }

  private generateResponseWithUserContent(message: string, userContent: string): string {
    return `Based on your uploaded content and question about "${message}", here's what I can help with:\n\n📄 **From Your Documents:**\nI can see you've uploaded relevant financial information. Let me provide context-specific advice.`;
  }

  private generateCourseListResponse(courses: any[]): string {
    if (!courses || courses.length === 0) {
      return "📚 **No courses available at the moment.** Please check back later.";
    }

    let response = "📚 **Available Financial Literacy Courses**\n\n";
    courses.forEach((course, index) => {
      response += `**${index + 1}. ${course.title}**\n📊 Level: ${course.difficulty}\n⏱️ Duration: ${course.estimatedTime}\n\n`;
    });

    return response;
  }

  private generateChatModeResponse(): string {
    return "💬 **Chat Mode Activated!**\n\nI'm ready to answer your financial questions! Ask me about budgeting, investing, debt management, and more.";
  }
} 