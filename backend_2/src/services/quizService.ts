import { v4 as uuidv4 } from 'uuid';
import { 
  QuizQuestion, 
  QuizResponse, 
  QuizSession, 
  DiagnosticTest,
  QUIZ_CONFIG,
  QUIZ_TOPICS 
} from '../types';
import { logger } from '../utils/logger';

export class QuizService {
  private diagnosticQuestions: QuizQuestion[] = [];
  private microQuizzes: Record<string, QuizQuestion[]> = {};
  private sessions: Map<string, QuizSession> = new Map();

  constructor() {
    this.initializeQuizzes();
  }

  private initializeQuizzes() {
    // Initialize diagnostic test questions
    this.diagnosticQuestions = [
      {
        id: 'diag-1',
        question: 'What is the recommended emergency fund size?',
        options: ['1-2 months expenses', '3-6 months expenses', '12 months expenses', '24 months expenses'],
        correctAnswer: 1,
        explanation: '3-6 months of expenses is recommended for most people.',
        topicTag: QUIZ_TOPICS.EMERGENCY_FUND,
        difficulty: 'easy'
      },
      {
        id: 'diag-2',
        question: 'What does APR stand for?',
        options: ['Annual Percentage Rate', 'Average Payment Rate', 'Annual Principal Rate', 'Adjusted Payment Rate'],
        correctAnswer: 0,
        explanation: 'APR is Annual Percentage Rate, representing the yearly cost of borrowing.',
        topicTag: QUIZ_TOPICS.CREDIT_CARDS,
        difficulty: 'easy'
      },
      {
        id: 'diag-3',
        question: 'Which investment typically offers the highest long-term returns?',
        options: ['Savings account', 'Bonds', 'Stocks', 'CDs'],
        correctAnswer: 2,
        explanation: 'Stocks historically provide the highest long-term returns, though with higher risk.',
        topicTag: QUIZ_TOPICS.INVESTING,
        difficulty: 'medium'
      },
      {
        id: 'diag-4',
        question: 'What is compound interest?',
        options: ['Interest on principal only', 'Interest on interest', 'Simple interest calculation', 'Bank fee structure'],
        correctAnswer: 1,
        explanation: 'Compound interest is earning interest on both principal and previously earned interest.',
        topicTag: QUIZ_TOPICS.SAVINGS,
        difficulty: 'medium'
      },
      {
        id: 'diag-5',
        question: 'What percentage of income should typically go to housing costs?',
        options: ['10-15%', '20-25%', '25-30%', '35-40%'],
        correctAnswer: 2,
        explanation: 'The general rule is to spend no more than 25-30% of income on housing.',
        topicTag: QUIZ_TOPICS.BUDGETING,
        difficulty: 'easy'
      },
      {
        id: 'diag-6',
        question: 'What is diversification in investing?',
        options: ['Buying only one stock', 'Spreading investments across different assets', 'Day trading', 'Timing the market'],
        correctAnswer: 1,
        explanation: 'Diversification means spreading investments to reduce risk.',
        topicTag: QUIZ_TOPICS.INVESTING,
        difficulty: 'medium'
      },
      {
        id: 'diag-7',
        question: 'When should you start saving for retirement?',
        options: ['Age 50', 'Age 40', 'Age 30', 'As early as possible'],
        correctAnswer: 3,
        explanation: 'Starting early allows compound interest to work longer in your favor.',
        topicTag: QUIZ_TOPICS.RETIREMENT,
        difficulty: 'easy'
      },
      {
        id: 'diag-8',
        question: 'What is a credit score used for?',
        options: ['Tax calculations', 'Investment decisions', 'Loan eligibility and rates', 'Salary negotiations'],
        correctAnswer: 2,
        explanation: 'Credit scores determine loan eligibility and interest rates.',
        topicTag: QUIZ_TOPICS.CREDIT_CARDS,
        difficulty: 'easy'
      },
      {
        id: 'diag-9',
        question: 'What is the debt avalanche method?',
        options: ['Pay minimums on all debts', 'Pay highest interest rate debt first', 'Pay smallest balance first', 'Consolidate all debts'],
        correctAnswer: 1,
        explanation: 'Debt avalanche focuses on paying the highest interest rate debt first.',
        topicTag: QUIZ_TOPICS.DEBT_MANAGEMENT,
        difficulty: 'medium'
      },
      {
        id: 'diag-10',
        question: 'What is term life insurance?',
        options: ['Permanent coverage', 'Temporary coverage for specific period', 'Investment product', 'Health insurance'],
        correctAnswer: 1,
        explanation: 'Term life insurance provides coverage for a specific time period.',
        topicTag: QUIZ_TOPICS.INSURANCE,
        difficulty: 'medium'
      }
    ];

    // Initialize micro-quizzes by topic
    this.microQuizzes = {
      [QUIZ_TOPICS.BUDGETING]: [
        {
          id: 'budg-1',
          question: 'What is the 50/30/20 rule?',
          options: ['50% needs, 30% wants, 20% savings', '50% housing, 30% food, 20% other', '50% salary, 30% bonus, 20% tips', '50% stocks, 30% bonds, 20% cash'],
          correctAnswer: 0,
          explanation: 'The 50/30/20 rule allocates income: 50% needs, 30% wants, 20% savings.',
          topicTag: QUIZ_TOPICS.BUDGETING,
          difficulty: 'easy'
        },
        {
          id: 'budg-2',
          question: 'Which expense category should you prioritize first in your budget?',
          options: ['Entertainment', 'Essential needs (housing, food)', 'Luxury items', 'Hobbies'],
          correctAnswer: 1,
          explanation: 'Essential needs like housing, food, and utilities should always be prioritized first.',
          topicTag: QUIZ_TOPICS.BUDGETING,
          difficulty: 'easy'
        }
      ],
      [QUIZ_TOPICS.SAVINGS]: [
        {
          id: 'sav-1',
          question: 'What is a high-yield savings account?',
          options: ['Account with fees', 'Account with higher interest rates', 'Investment account', 'Checking account'],
          correctAnswer: 1,
          explanation: 'High-yield savings accounts offer higher interest rates than traditional savings.',
          topicTag: QUIZ_TOPICS.SAVINGS,
          difficulty: 'easy'
        },
        {
          id: 'sav-2',
          question: 'How often does compound interest typically compound in a savings account?',
          options: ['Annually', 'Monthly', 'Daily', 'All of the above are possible'],
          correctAnswer: 3,
          explanation: 'Compound interest can compound annually, monthly, daily, or even continuously depending on the account.',
          topicTag: QUIZ_TOPICS.SAVINGS,
          difficulty: 'medium'
        }
      ],
      [QUIZ_TOPICS.INVESTING]: [
        {
          id: 'inv-1',
          question: 'What is dollar-cost averaging?',
          options: ['Buying stocks at the lowest price', 'Investing the same amount regularly', 'Selling when prices are high', 'Day trading strategy'],
          correctAnswer: 1,
          explanation: 'Dollar-cost averaging means investing a fixed amount regularly, regardless of market conditions.',
          topicTag: QUIZ_TOPICS.INVESTING,
          difficulty: 'medium'
        },
        {
          id: 'inv-2',
          question: 'What does P/E ratio stand for?',
          options: ['Price/Earnings', 'Profit/Expense', 'Principal/Equity', 'Performance/Efficiency'],
          correctAnswer: 0,
          explanation: 'P/E ratio stands for Price-to-Earnings ratio, a valuation metric for stocks.',
          topicTag: QUIZ_TOPICS.INVESTING,
          difficulty: 'hard'
        }
      ],
      [QUIZ_TOPICS.DEBT_MANAGEMENT]: [
        {
          id: 'debt-1',
          question: 'What is the debt snowball method?',
          options: ['Pay highest interest first', 'Pay smallest balance first', 'Pay largest balance first', 'Pay minimum on all debts'],
          correctAnswer: 1,
          explanation: 'The debt snowball method focuses on paying off the smallest balance first for psychological motivation.',
          topicTag: QUIZ_TOPICS.DEBT_MANAGEMENT,
          difficulty: 'medium'
        },
        {
          id: 'debt-2',
          question: 'What is a good debt-to-income ratio?',
          options: ['Below 20%', 'Below 36%', 'Below 50%', 'Below 70%'],
          correctAnswer: 1,
          explanation: 'A debt-to-income ratio below 36% is generally considered healthy.',
          topicTag: QUIZ_TOPICS.DEBT_MANAGEMENT,
          difficulty: 'medium'
        }
      ],
      [QUIZ_TOPICS.EMERGENCY_FUND]: [
        {
          id: 'emerg-1',
          question: 'Where should you keep your emergency fund?',
          options: ['Stock market', 'High-yield savings account', 'Under your mattress', 'Cryptocurrency'],
          correctAnswer: 1,
          explanation: 'Emergency funds should be easily accessible in a high-yield savings account.',
          topicTag: QUIZ_TOPICS.EMERGENCY_FUND,
          difficulty: 'easy'
        },
        {
          id: 'emerg-2',
          question: 'What qualifies as a true emergency expense?',
          options: ['Vacation', 'New phone', 'Medical emergency', 'Holiday shopping'],
          correctAnswer: 2,
          explanation: 'True emergencies are unexpected, necessary expenses like medical bills or job loss.',
          topicTag: QUIZ_TOPICS.EMERGENCY_FUND,
          difficulty: 'easy'
        }
      ]
    };
  }

  async getDiagnosticTest(): Promise<DiagnosticTest> {
    return {
      questions: this.diagnosticQuestions,
      totalQuestions: QUIZ_CONFIG.DIAGNOSTIC_QUESTIONS_COUNT,
      passingScore: QUIZ_CONFIG.PASSING_SCORE_PERCENTAGE
    };
  }

  async getMicroQuiz(topicTag: string): Promise<QuizQuestion | null> {
    const quizzes = this.microQuizzes[topicTag];
    if (!quizzes || quizzes.length === 0) {
      return null;
    }
    
    // Return a random quiz from the topic
    const randomIndex = Math.floor(Math.random() * quizzes.length);
    return quizzes[randomIndex];
  }

  async shouldInjectQuiz(sessionId: string): Promise<boolean> {
    const session = this.sessions.get(sessionId);
    if (!session) {
      return false;
    }

    // Temporary: Use shorter interval for testing (every 2 messages instead of 5)
    const interval = 2; // QUIZ_CONFIG.MICRO_QUIZ_INTERVAL;
    const shouldInject = session.messageCount > 0 && session.messageCount % interval === 0;
    
    logger.info('Quiz injection check', {
      sessionId,
      messageCount: session.messageCount,
      interval,
      shouldInject,
      completedPreTest: session.completedPreTest
    });
    
    return shouldInject;
  }

  async getOrCreateSession(userId: string, sessionId?: string): Promise<QuizSession> {
    const id = sessionId || uuidv4();
    
    // Temporary: Force reset all sessions to show diagnostic test
    // Remove this in production
    if (this.sessions.has(id)) {
      this.sessions.delete(id);
    }
    
    const newSession: QuizSession = {
      userId,
      sessionId: id,
      messageCount: 0,
      quizAttempts: 0,
      startTime: new Date().toISOString(),
      lastActivity: new Date().toISOString(),
      completedPreTest: false
    };

    this.sessions.set(id, newSession);
    return newSession;
  }

  async updateSession(sessionId: string, updates: Partial<QuizSession>): Promise<void> {
    const session = this.sessions.get(sessionId);
    if (session) {
      Object.assign(session, updates);
      session.lastActivity = new Date().toISOString();
    }
  }

  async incrementMessageCount(sessionId: string): Promise<void> {
    const session = this.sessions.get(sessionId);
    if (session) {
      session.messageCount++;
      session.lastActivity = new Date().toISOString();
    }
  }

  async logQuizResponse(response: QuizResponse): Promise<void> {
    logger.info('Quiz response logged', {
      userId: response.userId,
      quizId: response.quizId,
      correct: response.correct,
      topicTag: response.topicTag
    });

    // Update session quiz attempts
    const session = this.sessions.get(response.sessionId);
    if (session) {
      session.quizAttempts++;
      session.lastActivity = new Date().toISOString();
    }

    // TODO: Implement Google Sheets logging
    // TODO: Implement database logging
  }

  // TODO: Phase 3 - AI Integration
  async generateContextualQuiz(recentMessages: string[]): Promise<QuizQuestion | null> {
    // TODO: Use AI to generate contextual quizzes based on recent chat messages
    // For now, return a random quiz
    const topics = Object.keys(this.microQuizzes);
    const randomTopic = topics[Math.floor(Math.random() * topics.length)];
    return this.getMicroQuiz(randomTopic);
  }
} 