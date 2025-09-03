import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { loginUser, registerUser, logoutUser } from '../../utils/chatWidget/api'
import { getSessionChatCount } from '../../utils/chatWidget/api';
import { submitDiagnosticQuiz } from '../../utils/chatWidget/api';
import { QuizResponse } from '../../types';

// Mock fetch globally
global.fetch = vi.fn()

describe('API Functions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('loginUser', () => {
    it('should make successful login request with timing', async () => {
      const mockResponse = {
        access_token: 'test-access-token',
        refresh_token: 'test-refresh-token',
        user: { id: 'test-user-id' }
      }

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response)

      const startTime = performance.now()
      const result = await loginUser('test@example.com', 'password123')
      const endTime = performance.now()

      const executionTime = endTime - startTime

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/user/login'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify({
            email: 'test@example.com',
            password: 'password123',
          }),
        })
      )

      expect(result).toEqual(mockResponse)
      expect(executionTime).toBeLessThan(5000) // Should complete within 5 seconds
    })

    it('should handle login error with timing', async () => {
      const errorMessage = 'Invalid credentials'
      
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: errorMessage }),
      } as Response)

      const startTime = performance.now()
      
      await expect(loginUser('test@example.com', 'wrongpassword')).rejects.toThrow(errorMessage)
      
      const endTime = performance.now()
      const executionTime = endTime - startTime

      expect(executionTime).toBeLessThan(3000) // Error should be handled quickly
    })

    it('should handle network timeout', async () => {
      vi.mocked(fetch).mockImplementationOnce(() => 
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Network timeout')), 100)
        )
      )

      const startTime = performance.now()
      
      await expect(loginUser('test@example.com', 'password123')).rejects.toThrow('Network timeout')
      
      const endTime = performance.now()
      const executionTime = endTime - startTime

      expect(executionTime).toBeLessThan(200) // Should timeout quickly in test
    })
  })

  describe('registerUser', () => {
    it('should make successful registration request with timing', async () => {
      const mockResponse = {
        access_token: 'test-access-token',
        refresh_token: 'test-refresh-token',
        user: { id: 'test-user-id' }
      }

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response)

      const startTime = performance.now()
      const result = await registerUser('test@example.com', 'password123', 'John', 'Doe')
      const endTime = performance.now()

      const executionTime = endTime - startTime

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/user/register'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify({
            email: 'test@example.com',
            password: 'password123',
            first_name: 'John',
            last_name: 'Doe',
          }),
        })
      )

      expect(result).toEqual(mockResponse)
      expect(executionTime).toBeLessThan(5000) // Should complete within 5 seconds
    })

    it('should handle registration error with timing', async () => {
      const errorMessage = 'Email already exists'
      
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 409,
        json: async () => ({ detail: errorMessage }),
      } as Response)

      const startTime = performance.now()
      
      await expect(registerUser('existing@example.com', 'password123', 'John', 'Doe'))
        .rejects.toThrow(errorMessage)
      
      const endTime = performance.now()
      const executionTime = endTime - startTime

      expect(executionTime).toBeLessThan(3000) // Error should be handled quickly
    })
  })

  describe('logoutUser', () => {
    it('should make successful logout request with timing', async () => {
      const mockResponse = { success: true }

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response)

      const startTime = performance.now()
      const result = await logoutUser('test-refresh-token')
      const endTime = performance.now()

      const executionTime = endTime - startTime

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/user/logout'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify({
            refresh_token: 'test-refresh-token',
          }),
        })
      )

      expect(result).toEqual(mockResponse)
      expect(executionTime).toBeLessThan(3000) // Should complete within 3 seconds
    })

    it('should handle logout error with timing', async () => {
      const errorMessage = 'Invalid refresh token'
      
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: errorMessage }),
      } as Response)

      const startTime = performance.now()
      
      await expect(logoutUser('invalid-refresh-token')).rejects.toThrow(errorMessage)
      
      const endTime = performance.now()
      const executionTime = endTime - startTime

      expect(executionTime).toBeLessThan(3000) // Error should be handled quickly
    })

    it('should handle logout with expired refresh token', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Refresh token expired' }),
      } as Response)

      const startTime = performance.now()
      
      await expect(logoutUser('expired-refresh-token')).rejects.toThrow('Refresh token expired')
      
      const endTime = performance.now()
      const executionTime = endTime - startTime

      expect(executionTime).toBeLessThan(3000) // Should handle expired token quickly
    })
  })

  describe('Performance Benchmarks', () => {
    it('should handle multiple concurrent login requests efficiently', async () => {
      const mockResponse = {
        access_token: 'test-access-token',
        refresh_token: 'test-refresh-token',
        user: { id: 'test-user-id' }
      }

      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      } as Response)

      const startTime = performance.now()
      
      // Make multiple concurrent requests
      const promises = Array.from({ length: 5 }, () => 
        loginUser('test@example.com', 'password123')
      )
      
      const results = await Promise.all(promises)
      const endTime = performance.now()

      const totalTime = endTime - startTime

      expect(results).toHaveLength(5)
      expect(fetch).toHaveBeenCalledTimes(5)
      expect(totalTime).toBeLessThan(10000) // Should handle 5 concurrent requests within 10 seconds
    })

    it('should handle rapid logout requests efficiently', async () => {
      const mockResponse = { success: true }

      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      } as Response)

      const startTime = performance.now()
      
      // Make rapid logout requests
      const promises = Array.from({ length: 3 }, () => 
        logoutUser('test-refresh-token')
      )
      
      const results = await Promise.all(promises)
      const endTime = performance.now()

      const totalTime = endTime - startTime

      expect(results).toHaveLength(3)
      expect(fetch).toHaveBeenCalledTimes(3)
      expect(totalTime).toBeLessThan(5000) // Should handle 3 rapid logout requests within 5 seconds
    })

    it('should handle mixed API calls efficiently', async () => {
      const loginResponse = {
        access_token: 'test-access-token',
        refresh_token: 'test-refresh-token',
        user: { id: 'test-user-id' }
      }
      const registerResponse = {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        user: { id: 'new-user-id' }
      }
      const logoutResponse = { success: true }

      vi.mocked(fetch)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => loginResponse,
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => registerResponse,
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => logoutResponse,
        } as Response)

      const startTime = performance.now()
      
      // Mixed API calls
      const [loginResult, registerResult, logoutResult] = await Promise.all([
        loginUser('test@example.com', 'password123'),
        registerUser('new@example.com', 'password123', 'Jane', 'Doe'),
        logoutUser('test-refresh-token')
      ])
      
      const endTime = performance.now()
      const totalTime = endTime - startTime

      expect(loginResult).toEqual(loginResponse)
      expect(registerResult).toEqual(registerResponse)
      expect(logoutResult).toEqual(logoutResponse)
      expect(fetch).toHaveBeenCalledTimes(3)
      expect(totalTime).toBeLessThan(8000) // Should handle mixed calls within 8 seconds
    })
  })

  describe('Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      vi.mocked(fetch).mockRejectedValueOnce(new Error('Network error'))

      const startTime = performance.now()
      
      await expect(loginUser('test@example.com', 'password123'))
        .rejects.toThrow('Network error')
      
      const endTime = performance.now()
      const executionTime = endTime - startTime

      expect(executionTime).toBeLessThan(1000) // Should handle network errors quickly
    })

    it('should handle malformed JSON responses', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        json: async () => { throw new Error('Invalid JSON') },
      } as Response)

      const startTime = performance.now()
      
      await expect(loginUser('test@example.com', 'password123'))
        .rejects.toThrow('Login failed')
      
      const endTime = performance.now()
      const executionTime = endTime - startTime

      expect(executionTime).toBeLessThan(1000) // Should handle malformed responses quickly
    })

    it('should handle server errors with timing', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Internal server error' }),
      } as Response)

      const startTime = performance.now()
      
      await expect(loginUser('test@example.com', 'password123'))
        .rejects.toThrow('Internal server error')
      
      const endTime = performance.now()
      const executionTime = endTime - startTime

      expect(executionTime).toBeLessThan(3000) // Should handle server errors within 3 seconds
    })
  })
}) 

describe('getSessionChatCount', () => {
  const config = { apiUrl: '', userId: 'test-user', sessionId: 'test-session' };
  const sessionId = 'test-session';
  const endpoint = `/api/chat/session/${sessionId}/chat-count`;

  beforeEach(() => {
    global.fetch = vi.fn();
  });

  it('returns should_generate_quiz true at 3 messages', async () => {
    (fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        session_id: sessionId,
        user_id: config.userId,
        chat_count: 3,
        should_generate_quiz: true,
        messages_until_quiz: 0
      })
    });
    const result = await getSessionChatCount(config, sessionId);
    expect(result.should_generate_quiz).toBe(true);
    expect(result.messages_until_quiz).toBe(0);
  });

  it('returns should_generate_quiz true at 6 messages', async () => {
    (fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        session_id: sessionId,
        user_id: config.userId,
        chat_count: 6,
        should_generate_quiz: true,
        messages_until_quiz: 0
      })
    });
    const result = await getSessionChatCount(config, sessionId);
    expect(result.should_generate_quiz).toBe(true);
    expect(result.messages_until_quiz).toBe(0);
  });

  it('returns should_generate_quiz false at 4 and 5 messages', async () => {
    for (const count of [4, 5]) {
      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          session_id: sessionId,
          user_id: config.userId,
          chat_count: count,
          should_generate_quiz: false,
          messages_until_quiz: 3 - (count % 3)
        })
      });
      const result = await getSessionChatCount(config, sessionId);
      expect(result.should_generate_quiz).toBe(false);
      expect(result.messages_until_quiz).toBe(3 - (count % 3));
    }
  });

  it('returns should_generate_quiz true at 9 messages', async () => {
    (fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        session_id: sessionId,
        user_id: config.userId,
        chat_count: 9,
        should_generate_quiz: true,
        messages_until_quiz: 0
      })
    });
    const result = await getSessionChatCount(config, sessionId);
    expect(result.should_generate_quiz).toBe(true);
    expect(result.messages_until_quiz).toBe(0);
  });

  it('returns correct chat count and quiz flag (success)', async () => {
    (fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        session_id: sessionId,
        user_id: config.userId,
        chat_count: 3,
        should_generate_quiz: true,
        messages_until_quiz: 0
      })
    });
    const result = await getSessionChatCount(config, sessionId);
    expect(result.chat_count).toBe(3);
    expect(result.should_generate_quiz).toBe(true);
    expect(result.messages_until_quiz).toBe(0);
  });

  it('returns below threshold', async () => {
    (fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        session_id: sessionId,
        user_id: config.userId,
        chat_count: 2,
        should_generate_quiz: false,
        messages_until_quiz: 1
      })
    });
    const result = await getSessionChatCount(config, sessionId);
    expect(result.chat_count).toBe(2);
    expect(result.should_generate_quiz).toBe(false);
    expect(result.messages_until_quiz).toBe(1);
  });

  it('returns no messages', async () => {
    (fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        session_id: sessionId,
        user_id: config.userId,
        chat_count: 0,
        should_generate_quiz: false,
        messages_until_quiz: 3
      })
    });
    const result = await getSessionChatCount(config, sessionId);
    expect(result.chat_count).toBe(0);
    expect(result.should_generate_quiz).toBe(false);
    expect(result.messages_until_quiz).toBe(3);
  });

  it('handles session not found (404)', async () => {
    (fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Session not found' })
    });
    await expect(getSessionChatCount(config, sessionId)).rejects.toThrow('Session not found');
  });

  it('handles database error (500)', async () => {
    (fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ detail: 'Failed to get session chat count' })
    });
    await expect(getSessionChatCount(config, sessionId)).rejects.toThrow('Failed to get session chat count');
  });

  it('returns correct chat count for mixed messages', async () => {
    (fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        session_id: sessionId,
        user_id: config.userId,
        chat_count: 4,
        should_generate_quiz: true,
        messages_until_quiz: 0
      })
    });
    const result = await getSessionChatCount(config, sessionId);
    expect(result.chat_count).toBe(4);
    expect(result.should_generate_quiz).toBe(true);
    expect(result.messages_until_quiz).toBe(0);
  });
}); 

describe('submitDiagnosticQuiz', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should submit diagnostic quiz with all required data fields', async () => {
    // Mock successful response
    const mockResponse = { ok: true, json: () => Promise.resolve({ data: { success: true } }) };
    (global.fetch as vi.Mock).mockResolvedValue(mockResponse);

    const config = {
      apiUrl: 'http://localhost:8000',
      userId: 'test-user-123',
      sessionId: 'test-session-123'
    };

    const quiz_id = 'quiz_test_123';
    const userId = 'test-user-123';
    
    const questions = [
      {
        id: 'q1',
        question: 'What is the best investment strategy?',
        options: ['Diversify', 'Put all in one stock', 'Avoid investing', 'Only cash'],
        correctAnswer: 0,
        explanation: 'Diversification reduces risk by spreading investments across different assets.',
        topicTag: 'Investing',
        difficulty: 'medium' as const
      },
      {
        id: 'q2',
        question: 'What is budgeting?',
        options: ['Spending without limits', 'Tracking income and expenses', 'Ignoring bills', 'Gambling'],
        correctAnswer: 1,
        explanation: 'Budgeting helps you track your income and expenses to manage your money effectively.',
        topicTag: 'Budgeting',
        difficulty: 'easy' as const
      }
    ];

    const answers = [0, 1]; // User answered correctly for both questions

    // Transform questions and answers into QuizResponse format for the new API
    const quizResponses = questions.map((question, index) => {
      const answerIdx = answers[index];
      const isCorrect = answerIdx === question.correctAnswer;
      
      return {
        quiz_id,
        selected_option: String.fromCharCode(65 + answerIdx), // 'A', 'B', 'C', 'D'
        correct: isCorrect,
        topic: question.topicTag || '',
        
        correctAnswer: String.fromCharCode(65 + question.correctAnswer), // 'A', 'B', 'C', 'D'
        question: question.question,
        choices: question.options.reduce((acc, option, idx) => {
          acc[String.fromCharCode(65 + idx)] = option; // 'A': 'option text', 'B': 'option text', etc.
          return acc;
        }, {} as Record<string, string>),
        difficulty: question.difficulty || 'medium'
      };
    });

    await submitDiagnosticQuiz(config, quiz_id, quizResponses, userId);

    // Verify fetch was called with correct data
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/quiz/submit',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Content-Type': 'application/json'
        }),
        body: expect.stringContaining('"quiz_type":"diagnostic"')
      })
    );

    // Parse the body to verify all fields are present
    const callArgs = (global.fetch as vi.Mock).mock.calls[0];
    const body = JSON.parse(callArgs[1].body);

    expect(body).toEqual({
      user_id: 'test-user-123',
      quiz_type: 'diagnostic',
      session_id: 'test-session-123',
      responses: [
        {
          quiz_id: 'quiz_test_123',
          selected_option: 'A',
          correct: true,
          topic: 'Investing'
        },
        {
          quiz_id: 'quiz_test_123',
          selected_option: 'B',
          correct: true,
          topic: 'Budgeting'
        }
      ]
    });
  });

  it('should handle incorrect answers correctly', async () => {
    const mockResponse = { ok: true, json: () => Promise.resolve({ data: { success: true } }) };
    (global.fetch as vi.Mock).mockResolvedValue(mockResponse);

    const config = {
      apiUrl: 'http://localhost:8000',
      userId: 'test-user-123',
      sessionId: 'test-session-123'
    };

    const quiz_id = 'quiz_test_123';
    const userId = 'test-user-123';
    
    const questions = [
      {
        id: 'q1',
        question: 'What is the best investment strategy?',
        options: ['Diversify', 'Put all in one stock', 'Avoid investing', 'Only cash'],
        correctAnswer: 0,
        explanation: 'Diversification reduces risk by spreading investments across different assets.',
        topicTag: 'Investing',
        difficulty: 'medium' as const
      }
    ];

    const answers = [2]; // User answered incorrectly (selected 'C' instead of 'A')

    // Transform questions and answers into QuizResponse format for the new API
    const quizResponses = questions.map((question, index) => {
      const answerIdx = answers[index];
      const isCorrect = answerIdx === question.correctAnswer;
      
      return {
        quiz_id,
        selected_option: String.fromCharCode(65 + answerIdx), // 'A', 'B', 'C', 'D'
        correct: isCorrect,
        topic: question.topicTag || '',
        
        correctAnswer: String.fromCharCode(65 + question.correctAnswer), // 'A', 'B', 'C', 'D'
        question: question.question,
        choices: question.options.reduce((acc, option, idx) => {
          acc[String.fromCharCode(65 + idx)] = option; // 'A': 'option text', 'B': 'option text', etc.
          return acc;
        }, {} as Record<string, string>),
        difficulty: question.difficulty || 'medium'
      };
    });

    await submitDiagnosticQuiz(config, quiz_id, quizResponses, userId);

    const callArgs = (global.fetch as vi.Mock).mock.calls[0];
    const body = JSON.parse(callArgs[1].body);

    expect(body.responses[0]).toEqual({
      quiz_id: 'quiz_test_123',
      selected_option: 'C',
      correct: false, // Should be false since user selected wrong answer
      topic: 'Investing',
      explanation: 'Diversification reduces risk by spreading investments across different assets.',
      correctAnswer: 'A',
      question_data: {
        question: 'What is the best investment strategy?',
        choices: ['Diversify', 'Put all in one stock', 'Avoid investing', 'Only cash'],
        correctAnswer: 'A',
        explanation: 'Diversification reduces risk by spreading investments across different assets.',
        topic: 'Investing',
        difficulty: 'medium'
      }
    });
  });

  it('should throw error if not all questions are answered', async () => {
    const config = {
      apiUrl: 'http://localhost:8000',
      userId: 'test-user-123',
      sessionId: 'test-session-123'
    };

    const quiz_id = 'quiz_test_123';
    const userId = 'test-user-123';
    
    const questions = [
      {
        id: 'q1',
        question: 'What is the best investment strategy?',
        options: ['Diversify', 'Put all in one stock', 'Avoid investing', 'Only cash'],
        correctAnswer: 0,
        explanation: 'Diversification reduces risk by spreading investments across different assets.',
        topicTag: 'Investing',
        difficulty: 'medium' as const
      }
    ];

    const answers = [-1]; // Invalid answer index

    // Transform questions and answers into QuizResponse format for the new API
    const quizResponses = questions.map((question, index) => {
      const answerIdx = answers[index];
      const isCorrect = answerIdx === question.correctAnswer;
      
      return {
        quiz_id,
        selected_option: String.fromCharCode(65 + answerIdx), // 'A', 'B', 'C', 'D'
        correct: isCorrect,
        topic: question.topicTag || '',
        
        correctAnswer: String.fromCharCode(65 + question.correctAnswer), // 'A', 'B', 'C', 'D'
        question: question.question,
        choices: question.options.reduce((acc, option, idx) => {
          acc[String.fromCharCode(65 + idx)] = option; // 'A': 'option text', 'B': 'option text', etc.
          return acc;
        }, {} as Record<string, string>),
        difficulty: question.difficulty || 'medium'
      };
    });

    await expect(
      submitDiagnosticQuiz(config, quiz_id, quizResponses, userId)
    ).rejects.toThrow('All questions must be answered before submitting.');
  });

  it('should handle missing optional fields gracefully', async () => {
    const mockResponse = { ok: true, json: () => Promise.resolve({ data: { success: true } }) };
    (global.fetch as vi.Mock).mockResolvedValue(mockResponse);

    const config = {
      apiUrl: 'http://localhost:8000',
      userId: 'test-user-123',
      sessionId: 'test-session-123'
    };

    const quiz_id = 'quiz_test_123';
    const userId = 'test-user-123';
    
    const questions = [
      {
        id: 'q1',
        question: 'What is the best investment strategy?',
        options: ['Diversify', 'Put all in one stock', 'Avoid investing', 'Only cash'],
        correctAnswer: 0,
        explanation: '', // Empty explanation
        topicTag: '', // Empty topic
        difficulty: undefined // Missing difficulty
      }
    ];

    const answers = [0];

    // Transform questions and answers into QuizResponse format for the new API
    const quizResponses = questions.map((question, index) => {
      const answerIdx = answers[index];
      const isCorrect = answerIdx === question.correctAnswer;
      
      return {
        quiz_id,
        selected_option: String.fromCharCode(65 + answerIdx), // 'A', 'B', 'C', 'D'
        correct: isCorrect,
        topic: question.topicTag || '',
        
        correctAnswer: String.fromCharCode(65 + question.correctAnswer), // 'A', 'B', 'C', 'D'
        question: question.question,
        choices: question.options.reduce((acc, option, idx) => {
          acc[String.fromCharCode(65 + idx)] = option; // 'A': 'option text', 'B': 'option text', etc.
          return acc;
        }, {} as Record<string, string>),
        difficulty: question.difficulty || 'medium'
      };
    });

    await submitDiagnosticQuiz(config, quiz_id, quizResponses, userId);

    const callArgs = (global.fetch as vi.Mock).mock.calls[0];
    const body = JSON.parse(callArgs[1].body);

    expect(body.responses[0]).toEqual({
      quiz_id: 'quiz_test_123',
      selected_option: 'A',
      correct: true,
      topic: '',
      explanation: '',
      correctAnswer: 'A',
      question_data: {
        question: 'What is the best investment strategy?',
        choices: ['Diversify', 'Put all in one stock', 'Avoid investing', 'Only cash'],
        correctAnswer: 'A',
        explanation: '',
        topic: '',
        difficulty: 'medium' // Should default to 'medium'
      }
    });
  });
}); 