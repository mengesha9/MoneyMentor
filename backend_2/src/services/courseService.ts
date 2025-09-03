import { v4 as uuidv4 } from 'uuid';
import { 
  Course, 
  CoursePage, 
  CourseProgress, 
  CourseSession,
  QuizQuestion,
  QUIZ_CONFIG,
  QUIZ_TOPICS 
} from '../types';
import { logger } from '../utils/logger';

export class CourseService {
  private courses: Map<string, Course> = new Map();
  private courseSessions: Map<string, CourseSession> = new Map();
  private courseProgress: Map<string, Map<string, CourseProgress>> = new Map(); // userId -> courseId -> progress

  constructor() {
    this.initializeCourses();
  }

  private initializeCourses() {
    // Course 1: Budgeting Basics
    const budgetingCourse: Course = {
      id: 'course-budgeting-basics',
      title: 'Budgeting Basics',
      description: 'Learn the fundamentals of creating and managing a personal budget',
      difficulty: 'beginner',
      topicTag: QUIZ_TOPICS.BUDGETING,
      estimatedTime: '10-15 minutes',
      pages: [
        {
          id: 'budgeting-page-1',
          title: 'What is Budgeting?',
          content: `# What is Budgeting?

**Budgeting** is the process of creating a plan for how you'll spend your money. Think of it as a roadmap for your finances that helps you:

• **Track your income** - Know exactly how much money comes in
• **Monitor your expenses** - See where your money goes
• **Plan for the future** - Set aside money for goals and emergencies
• **Avoid overspending** - Stay within your means

## Why Budget?

Without a budget, it's easy to:
- Spend more than you earn
- Miss opportunities to save
- Feel stressed about money
- Struggle to reach financial goals

**Key Point**: A budget isn't about restricting yourself—it's about giving yourself permission to spend on what matters most to you while securing your financial future.`,
          pageNumber: 1,
          totalPages: 3
        },
        {
          id: 'budgeting-page-2',
          title: 'The 50/30/20 Rule',
          content: `# The 50/30/20 Rule

One of the most popular and effective budgeting methods is the **50/30/20 rule**:

## 50% - Needs (Essential Expenses)
• Housing (rent/mortgage)
• Utilities (electricity, water, gas)
• Groceries
• Transportation
• Insurance
• Minimum debt payments

## 30% - Wants (Discretionary Spending)
• Dining out
• Entertainment
• Hobbies
• Shopping
• Subscriptions
• Travel

## 20% - Savings & Debt Repayment
• Emergency fund
• Retirement savings
• Extra debt payments
• Investment accounts

**Example**: If you earn $4,000/month:
- $2,000 for needs
- $1,200 for wants  
- $800 for savings/debt

This rule provides a simple framework that you can adjust based on your specific situation.`,
          pageNumber: 2,
          totalPages: 3
        },
        {
          id: 'budgeting-page-3',
          title: 'Creating Your First Budget',
          content: `# Creating Your First Budget

Follow these **5 simple steps** to create your budget:

## Step 1: Calculate Your Income
List all sources of money coming in:
• Salary (after taxes)
• Side hustles
• Investment returns
• Any other regular income

## Step 2: Track Your Expenses
For one month, write down everything you spend:
• Use apps like Mint or YNAB
• Check bank statements
• Keep receipts
• Note cash purchases

## Step 3: Categorize Expenses
Group your spending into:
• **Fixed costs** (rent, insurance)
• **Variable needs** (groceries, gas)
• **Wants** (entertainment, dining out)

## Step 4: Apply the 50/30/20 Rule
Allocate your income using the percentages we learned.

## Step 5: Review and Adjust
• Check your budget weekly
• Adjust categories as needed
• Don't be too strict initially
• Focus on building the habit

**Remember**: Your first budget won't be perfect. The goal is to start tracking and improve over time!`,
          pageNumber: 3,
          totalPages: 3
        }
      ],
      quizQuestions: [
        {
          id: 'budgeting-quiz-1',
          question: 'According to the 50/30/20 rule, what percentage of income should go to needs?',
          options: ['30%', '50%', '20%', '40%'],
          correctAnswer: 1,
          explanation: 'The 50/30/20 rule allocates 50% of income to essential needs like housing, utilities, and groceries.',
          topicTag: QUIZ_TOPICS.BUDGETING,
          difficulty: 'easy'
        },
        {
          id: 'budgeting-quiz-2',
          question: 'Which of these is considered a "want" rather than a "need"?',
          options: ['Rent payment', 'Groceries', 'Netflix subscription', 'Car insurance'],
          correctAnswer: 2,
          explanation: 'Netflix subscription is entertainment and falls under the "wants" category, while the others are essential needs.',
          topicTag: QUIZ_TOPICS.BUDGETING,
          difficulty: 'easy'
        },
        {
          id: 'budgeting-quiz-3',
          question: 'What is the first step in creating a budget?',
          options: ['Track expenses', 'Calculate income', 'Set savings goals', 'Pay off debt'],
          correctAnswer: 1,
          explanation: 'You need to know how much money you have coming in before you can plan how to spend it.',
          topicTag: QUIZ_TOPICS.BUDGETING,
          difficulty: 'easy'
        }
      ]
    };

    // Course 2: Emergency Fund Essentials
    const emergencyFundCourse: Course = {
      id: 'course-emergency-fund',
      title: 'Emergency Fund Essentials',
      description: 'Build a financial safety net to protect yourself from unexpected expenses',
      difficulty: 'beginner',
      topicTag: QUIZ_TOPICS.EMERGENCY_FUND,
      estimatedTime: '8-12 minutes',
      pages: [
        {
          id: 'emergency-page-1',
          title: 'Why You Need an Emergency Fund',
          content: `# Why You Need an Emergency Fund

An **emergency fund** is money set aside specifically for unexpected expenses or financial emergencies. It's your financial safety net.

## What Qualifies as an Emergency?

**True emergencies include**:
• Job loss or reduced income
• Medical emergencies
• Major car repairs
• Home repairs (roof, plumbing, etc.)
• Family emergencies

**NOT emergencies**:
• Vacations
• Holiday shopping
• New clothes
• Planned expenses

## Why It Matters

Without an emergency fund, unexpected expenses can:
- Force you into debt
- Derail your financial goals
- Create stress and anxiety
- Lead to poor financial decisions

**Peace of Mind**: Knowing you can handle unexpected expenses reduces financial stress and gives you confidence in your financial stability.`,
          pageNumber: 1,
          totalPages: 2
        },
        {
          id: 'emergency-page-2',
          title: 'Building Your Emergency Fund',
          content: `# Building Your Emergency Fund

## How Much Do You Need?

**Starter Goal**: $1,000 minimum
**Full Goal**: 3-6 months of living expenses

**Calculate your target**:
1. Add up monthly essential expenses
2. Multiply by 3-6 months
3. Start with $1,000 if the full amount feels overwhelming

## Where to Keep It

**Best options**:
• **High-yield savings account** - Easy access, earns interest
• **Money market account** - Slightly higher rates
• **Short-term CDs** - For portion you won't need immediately

**Avoid**:
• Checking accounts (too easy to spend)
• Investment accounts (too risky for emergencies)
• Cash at home (no growth, security risk)

## How to Build It

**Start small and be consistent**:
• Set up automatic transfers
• Save tax refunds and bonuses
• Use the "pay yourself first" principle
• Cut one expense and redirect that money
• Save loose change and small bills

**Example**: Saving $50/week = $2,600/year

Remember: Building an emergency fund takes time. Focus on consistency rather than the amount.`,
          pageNumber: 2,
          totalPages: 2
        }
      ],
      quizQuestions: [
        {
          id: 'emergency-quiz-1',
          question: 'How much should a full emergency fund cover?',
          options: ['1 month of expenses', '3-6 months of expenses', '1 year of expenses', '$10,000 minimum'],
          correctAnswer: 1,
          explanation: 'A full emergency fund should cover 3-6 months of living expenses to provide adequate protection.',
          topicTag: QUIZ_TOPICS.EMERGENCY_FUND,
          difficulty: 'easy'
        },
        {
          id: 'emergency-quiz-2',
          question: 'Where is the best place to keep your emergency fund?',
          options: ['Checking account', 'Investment account', 'High-yield savings account', 'Under your mattress'],
          correctAnswer: 2,
          explanation: 'A high-yield savings account provides easy access while earning interest, making it ideal for emergency funds.',
          topicTag: QUIZ_TOPICS.EMERGENCY_FUND,
          difficulty: 'easy'
        },
        {
          id: 'emergency-quiz-3',
          question: 'Which of these is NOT a true emergency?',
          options: ['Job loss', 'Medical emergency', 'Holiday shopping', 'Major car repair'],
          correctAnswer: 2,
          explanation: 'Holiday shopping is a planned expense, not an emergency. True emergencies are unexpected and necessary.',
          topicTag: QUIZ_TOPICS.EMERGENCY_FUND,
          difficulty: 'easy'
        }
      ]
    };

    // Course 3: Investing Fundamentals
    const investingCourse: Course = {
      id: 'course-investing-basics',
      title: 'Investing Fundamentals',
      description: 'Learn the basics of investing to grow your wealth over time',
      difficulty: 'intermediate',
      topicTag: QUIZ_TOPICS.INVESTING,
      estimatedTime: '15-20 minutes',
      prerequisites: ['course-budgeting-basics', 'course-emergency-fund'],
      pages: [
        {
          id: 'investing-page-1',
          title: 'Why Invest?',
          content: `# Why Invest?

**Investing** means putting your money to work to generate more money over time. It's essential for building long-term wealth.

## The Power of Compound Interest

**Albert Einstein** reportedly called compound interest "the eighth wonder of the world." Here's why:

When you invest, you earn returns not just on your original money, but also on the returns you've already earned.

**Example**: 
- Invest $1,000 at 7% annual return
- Year 1: $1,070 ($70 gain)
- Year 2: $1,145 ($75 gain on $1,070)
- Year 10: $1,967
- Year 30: $7,612

## Inflation Protection

**Inflation** reduces your purchasing power over time. Money sitting in low-interest accounts loses value.

- Average inflation: ~3% per year
- $1,000 today = ~$740 purchasing power in 10 years
- Investing helps your money grow faster than inflation

## Time is Your Greatest Asset

The earlier you start, the more time compound interest has to work:
- Start at 25: $500/month = $1.37M by 65
- Start at 35: $500/month = $679K by 65
- **10-year delay costs $691,000!**`,
          pageNumber: 1,
          totalPages: 3
        },
        {
          id: 'investing-page-2',
          title: 'Types of Investments',
          content: `# Types of Investments

## Stocks (Equities)
**What**: Ownership shares in companies
**Risk**: High
**Potential Return**: 8-10% annually (historical average)
**Best For**: Long-term growth

## Bonds
**What**: Loans to companies or governments
**Risk**: Low to moderate
**Potential Return**: 3-5% annually
**Best For**: Stability and income

## Mutual Funds
**What**: Professionally managed collection of stocks/bonds
**Risk**: Varies by fund type
**Potential Return**: Varies (typically 6-8%)
**Best For**: Diversification without research

## Index Funds
**What**: Funds that track market indexes (like S&P 500)
**Risk**: Moderate
**Potential Return**: Market returns (~7-10%)
**Best For**: Low-cost, diversified investing

## ETFs (Exchange-Traded Funds)
**What**: Like mutual funds but trade like stocks
**Risk**: Varies
**Potential Return**: Varies
**Best For**: Flexibility and low costs

## Real Estate
**What**: Property investments
**Risk**: Moderate to high
**Potential Return**: 6-8% plus appreciation
**Best For**: Diversification and inflation protection`,
          pageNumber: 2,
          totalPages: 3
        },
        {
          id: 'investing-page-3',
          title: 'Getting Started',
          content: `# Getting Started with Investing

## Before You Invest

**Prerequisites checklist**:
✅ Have an emergency fund (3-6 months expenses)
✅ Pay off high-interest debt (credit cards)
✅ Have a stable income
✅ Understand your risk tolerance

## Investment Accounts

**401(k)**: Employer-sponsored retirement account
- Often includes employer matching
- Tax advantages
- Limited investment options

**IRA (Individual Retirement Account)**:
- Traditional IRA: Tax deduction now, pay taxes later
- Roth IRA: Pay taxes now, tax-free withdrawals in retirement

**Taxable Brokerage Account**:
- No contribution limits
- More flexibility
- Pay taxes on gains

## Simple Starting Strategy

**For Beginners**:
1. **Start with index funds** (S&P 500 or Total Market)
2. **Automate investments** ($100-500/month)
3. **Don't try to time the market**
4. **Stay consistent** through ups and downs
5. **Increase contributions** as income grows

## Key Principles

• **Diversify**: Don't put all eggs in one basket
• **Think long-term**: Ignore daily market fluctuations  
• **Keep costs low**: High fees eat into returns
• **Stay the course**: Time in market beats timing the market

**Remember**: Investing is a marathon, not a sprint. Start small, stay consistent, and let time work in your favor.`,
          pageNumber: 3,
          totalPages: 3
        }
      ],
      quizQuestions: [
        {
          id: 'investing-quiz-1',
          question: 'What is compound interest?',
          options: ['Interest paid only on the original investment', 'Interest earned on both principal and previous interest', 'A type of bank account', 'A government bond'],
          correctAnswer: 1,
          explanation: 'Compound interest is earning returns on both your original investment and the returns you\'ve already earned, creating exponential growth over time.',
          topicTag: QUIZ_TOPICS.INVESTING,
          difficulty: 'medium'
        },
        {
          id: 'investing-quiz-2',
          question: 'Which investment type typically offers the highest long-term returns?',
          options: ['Bonds', 'Savings accounts', 'Stocks', 'CDs'],
          correctAnswer: 2,
          explanation: 'Stocks historically provide the highest long-term returns, averaging 8-10% annually, though with higher risk.',
          topicTag: QUIZ_TOPICS.INVESTING,
          difficulty: 'medium'
        },
        {
          id: 'investing-quiz-3',
          question: 'What should you do before you start investing?',
          options: ['Buy the hottest stocks', 'Build an emergency fund', 'Quit your job', 'Take out a loan'],
          correctAnswer: 1,
          explanation: 'You should have an emergency fund and pay off high-interest debt before investing to ensure financial stability.',
          topicTag: QUIZ_TOPICS.INVESTING,
          difficulty: 'medium'
        }
      ]
    };

    // Advanced Portfolio Management Course
    const portfolioManagementCourse: Course = {
      id: 'portfolio-management',
      title: 'Advanced Portfolio Management',
      description: 'Master advanced investment strategies, portfolio optimization, and risk management techniques for experienced investors.',
      difficulty: 'advanced',
      topicTag: QUIZ_TOPICS.INVESTING,
      estimatedTime: '25-30 minutes',
      pages: [
        {
          id: 'portfolio-page-1',
          title: 'Asset Allocation Strategies',
          content: `# Asset Allocation Strategies

## Strategic vs. Tactical Allocation

**Strategic Asset Allocation** is your long-term investment plan based on your:
- Risk tolerance
- Time horizon
- Financial goals
- Age and life stage

**Tactical Asset Allocation** involves short-term adjustments to take advantage of market opportunities.

## Modern Portfolio Theory

Developed by Harry Markowitz, this theory suggests:
- **Diversification reduces risk** without sacrificing returns
- **Efficient frontier** represents optimal risk-return combinations
- **Correlation matters** - assets that move differently provide better diversification

## Age-Based Allocation Rules

### Traditional Rule: "100 minus your age"
- Age 30: 70% stocks, 30% bonds
- Age 50: 50% stocks, 50% bonds
- Age 65: 35% stocks, 65% bonds

### Modern Approach: "110 or 120 minus your age"
- Accounts for longer lifespans
- Age 30: 80-90% stocks, 10-20% bonds
- Age 50: 60-70% stocks, 30-40% bonds

## Asset Classes to Consider

1. **Domestic Stocks** (Large, Mid, Small Cap)
2. **International Stocks** (Developed and Emerging Markets)
3. **Bonds** (Government, Corporate, Municipal)
4. **Real Estate** (REITs)
5. **Commodities** (Gold, Oil, Agriculture)
6. **Alternative Investments** (Private Equity, Hedge Funds)`,
          pageNumber: 1,
          totalPages: 3
        },
        {
          id: 'portfolio-page-2',
          title: 'Risk Management & Rebalancing',
          content: `# Risk Management & Rebalancing

## Understanding Investment Risk

### Types of Risk
1. **Market Risk** - Overall market movements
2. **Specific Risk** - Company or sector-specific issues
3. **Interest Rate Risk** - Bond price sensitivity to rate changes
4. **Inflation Risk** - Purchasing power erosion
5. **Currency Risk** - Foreign exchange fluctuations
6. **Liquidity Risk** - Difficulty selling investments

## Risk Measurement Tools

### Standard Deviation
- Measures volatility
- Higher = more risky
- S&P 500 historical: ~15-20%

### Beta
- Measures sensitivity to market movements
- Beta = 1: Moves with market
- Beta > 1: More volatile than market
- Beta < 1: Less volatile than market

### Sharpe Ratio
- Risk-adjusted returns
- (Return - Risk-free rate) / Standard Deviation
- Higher is better

## Rebalancing Strategies

### Calendar Rebalancing
- **Quarterly**: Good for active investors
- **Semi-annually**: Balanced approach
- **Annually**: Simple, tax-efficient

### Threshold Rebalancing
- Rebalance when allocation drifts 5-10% from target
- More responsive to market changes
- May result in more frequent trading

### Rebalancing Benefits
- **Maintains risk level**
- **Forces "buy low, sell high"**
- **Prevents style drift**
- **Captures rebalancing premium**`,
          pageNumber: 2,
          totalPages: 3
        },
        {
          id: 'portfolio-page-3',
          title: 'Tax-Efficient Investing',
          content: `# Tax-Efficient Investing

## Account Types and Tax Treatment

### Tax-Advantaged Accounts
1. **401(k)/403(b)** - Pre-tax contributions, taxed on withdrawal
2. **Traditional IRA** - Pre-tax contributions (if eligible), taxed on withdrawal
3. **Roth IRA** - After-tax contributions, tax-free growth and withdrawals
4. **HSA** - Triple tax advantage (deductible, growth, withdrawals for medical)

### Taxable Accounts
- Dividends and interest taxed annually
- Capital gains taxed when realized
- Long-term vs. short-term capital gains rates

## Asset Location Strategy

### Tax-Inefficient Assets (Hold in Tax-Advantaged Accounts)
- **Bonds and bond funds** (high ordinary income)
- **REITs** (high dividend yields)
- **Actively managed funds** (high turnover)
- **International funds** (foreign tax credits)

### Tax-Efficient Assets (Hold in Taxable Accounts)
- **Index funds** (low turnover)
- **Individual stocks** (control timing of gains)
- **Tax-managed funds**
- **Municipal bonds** (for high earners)

## Tax-Loss Harvesting

### Process
1. Sell investments at a loss
2. Use losses to offset gains
3. Reduce taxable income (up to $3,000/year)
4. Carry forward excess losses

### Wash Sale Rule
- Cannot buy "substantially identical" security within 30 days
- Applies to spouse's accounts too
- Use similar (not identical) funds as replacements

## Advanced Strategies

### Tax-Efficient Fund Selection
- Choose funds with low turnover ratios
- Consider ETFs over mutual funds
- Look for tax-managed funds

### Charitable Giving
- Donate appreciated securities directly
- Avoid capital gains tax
- Get full fair market value deduction

### Estate Planning
- Step-up in basis at death
- Gifting strategies for high-net-worth individuals
- Trust structures for tax efficiency`,
          pageNumber: 3,
          totalPages: 3
        }
      ],
      quizQuestions: [
        {
          id: 'portfolio-quiz-1',
          question: 'What is the primary benefit of diversification according to Modern Portfolio Theory?',
          options: ['Guaranteed returns', 'Reduced risk without sacrificing expected returns', 'Higher returns with more risk', 'Elimination of all investment risk'],
          correctAnswer: 1,
          explanation: 'Modern Portfolio Theory shows that diversification can reduce risk without necessarily reducing expected returns by combining assets with different correlation patterns.',
          topicTag: QUIZ_TOPICS.INVESTING,
          difficulty: 'hard'
        },
        {
          id: 'portfolio-quiz-2',
          question: 'Which rebalancing strategy responds most quickly to market changes?',
          options: ['Annual calendar rebalancing', 'Quarterly calendar rebalancing', 'Threshold-based rebalancing', 'Buy and hold with no rebalancing'],
          correctAnswer: 2,
          explanation: 'Threshold-based rebalancing triggers when allocations drift beyond set limits, making it most responsive to market movements.',
          topicTag: QUIZ_TOPICS.INVESTING,
          difficulty: 'hard'
        },
        {
          id: 'portfolio-quiz-3',
          question: 'Which type of investment is generally best held in a taxable account for tax efficiency?',
          options: ['High-yield bonds', 'REITs', 'Actively managed mutual funds', 'Broad market index funds'],
          correctAnswer: 3,
          explanation: 'Index funds are tax-efficient due to low turnover and minimal distributions, making them suitable for taxable accounts.',
          topicTag: QUIZ_TOPICS.INVESTING,
          difficulty: 'hard'
        }
      ]
    };

    // Store courses
    this.courses.set(budgetingCourse.id, budgetingCourse);
    this.courses.set(emergencyFundCourse.id, emergencyFundCourse);
    this.courses.set(investingCourse.id, investingCourse);
    this.courses.set(portfolioManagementCourse.id, portfolioManagementCourse);
  }

  async getAllCourses(): Promise<Course[]> {
    return Array.from(this.courses.values());
  }

  async getCourse(courseId: string): Promise<Course | null> {
    return this.courses.get(courseId) || null;
  }

  async getCoursesForUser(userId: string): Promise<Course[]> {
    const userProgress = this.courseProgress.get(userId) || new Map();
    const allCourses = Array.from(this.courses.values());
    
    // Sort courses by difficulty and completion status
    return allCourses.sort((a, b) => {
      const aCompleted = userProgress.get(a.id)?.completed || false;
      const bCompleted = userProgress.get(b.id)?.completed || false;
      
      if (aCompleted !== bCompleted) {
        return aCompleted ? 1 : -1; // Incomplete courses first
      }
      
      const difficultyOrder = { beginner: 0, intermediate: 1, advanced: 2 };
      return difficultyOrder[a.difficulty] - difficultyOrder[b.difficulty];
    });
  }

  async startCourse(userId: string, sessionId: string, courseId: string): Promise<CourseSession | null> {
    const course = this.courses.get(courseId);
    if (!course) return null;

    const session: CourseSession = {
      userId,
      sessionId,
      activeCourse: course,
      currentPageIndex: 0,
      courseProgress: this.courseProgress.get(userId) || new Map(),
      mode: 'course'
    };

    this.courseSessions.set(sessionId, session);

    // Initialize progress if not exists
    if (!this.courseProgress.has(userId)) {
      this.courseProgress.set(userId, new Map());
    }

    const userProgress = this.courseProgress.get(userId)!;
    if (!userProgress.has(courseId)) {
      userProgress.set(courseId, {
        userId,
        sessionId,
        courseId,
        currentPageIndex: 0,
        completed: false,
        quizAttempts: 0,
        startTime: new Date().toISOString()
      });
    }

    return session;
  }

  async getSession(sessionId: string): Promise<CourseSession | null> {
    return this.courseSessions.get(sessionId) || null;
  }

  async navigateToPage(sessionId: string, pageIndex: number): Promise<CoursePage | null> {
    const session = this.courseSessions.get(sessionId);
    if (!session || !session.activeCourse) return null;

    if (pageIndex < 0 || pageIndex >= session.activeCourse.pages.length) {
      return null;
    }

    session.currentPageIndex = pageIndex;
    
    // Update progress
    const userProgress = this.courseProgress.get(session.userId);
    const courseProgress = userProgress?.get(session.activeCourse.id);
    if (courseProgress) {
      courseProgress.currentPageIndex = Math.max(courseProgress.currentPageIndex, pageIndex);
    }

    return session.activeCourse.pages[pageIndex];
  }

  async completeCourse(sessionId: string): Promise<QuizQuestion[]> {
    const session = this.courseSessions.get(sessionId);
    if (!session || !session.activeCourse) return [];

    // Return quiz questions for the course
    return session.activeCourse.quizQuestions;
  }

  async submitCourseQuiz(sessionId: string, answers: number[]): Promise<{
    score: number;
    passed: boolean;
    correctAnswers: number[];
    explanations: string[];
  }> {
    const session = this.courseSessions.get(sessionId);
    if (!session || !session.activeCourse) {
      throw new Error('No active course session');
    }

    const questions = session.activeCourse.quizQuestions;
    let correctCount = 0;
    const correctAnswers: number[] = [];
    const explanations: string[] = [];

    questions.forEach((question, index) => {
      correctAnswers.push(question.correctAnswer);
      explanations.push(question.explanation);
      if (answers[index] === question.correctAnswer) {
        correctCount++;
      }
    });

    const score = Math.round((correctCount / questions.length) * 100);
    const passed = score >= QUIZ_CONFIG.PASSING_SCORE_PERCENTAGE;

    // Update progress
    const userProgress = this.courseProgress.get(session.userId);
    const courseProgress = userProgress?.get(session.activeCourse.id);
    if (courseProgress) {
      courseProgress.quizAttempts++;
      courseProgress.quizScore = score;
      if (passed) {
        courseProgress.completed = true;
        courseProgress.completionTime = new Date().toISOString();
      }
    }

    logger.info('Course quiz completed', {
      userId: session.userId,
      courseId: session.activeCourse.id,
      score,
      passed,
      attempts: courseProgress?.quizAttempts
    });

    return { score, passed, correctAnswers, explanations };
  }

  async getRandomDiagnosticQuestions(count: number = QUIZ_CONFIG.DIAGNOSTIC_QUESTIONS_COUNT): Promise<QuizQuestion[]> {
    // Use dedicated diagnostic questions instead of course quiz questions
    const diagnosticQuestions: QuizQuestion[] = [
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
      }
    ];

    // Shuffle and take the requested count
    const shuffled = diagnosticQuestions.sort(() => 0.5 - Math.random());
    return shuffled.slice(0, count);
  }

  async endCourseSession(sessionId: string): Promise<void> {
    const session = this.courseSessions.get(sessionId);
    if (session) {
      session.mode = 'chat';
      session.activeCourse = undefined;
      session.currentPageIndex = 0;
    }
  }

  async getRecommendedCourses(diagnosticScore: number): Promise<Course[]> {
    const allCourses = Array.from(this.courses.values());
    
    // Recommend courses based on diagnostic score
    if (diagnosticScore >= 80) {
      // High score: Suggest advanced courses first, then intermediate
      return allCourses
        .filter(course => course.difficulty === 'advanced' || course.difficulty === 'intermediate')
        .sort((a, b) => {
          const difficultyOrder = { advanced: 0, intermediate: 1, beginner: 2 };
          return difficultyOrder[a.difficulty] - difficultyOrder[b.difficulty];
        });
    } else if (diagnosticScore >= 50) {
      // Medium score: Suggest intermediate courses first, then beginner and advanced
      return allCourses
        .sort((a, b) => {
          const difficultyOrder = { intermediate: 0, beginner: 1, advanced: 2 };
          return difficultyOrder[a.difficulty] - difficultyOrder[b.difficulty];
        });
    } else {
      // Low score: Suggest beginner courses first, then intermediate
      return allCourses
        .filter(course => course.difficulty === 'beginner' || course.difficulty === 'intermediate')
        .sort((a, b) => {
          const difficultyOrder = { beginner: 0, intermediate: 1, advanced: 2 };
          return difficultyOrder[a.difficulty] - difficultyOrder[b.difficulty];
        });
    }
  }
} 