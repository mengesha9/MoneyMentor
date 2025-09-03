import { 
  EngagementMetrics, 
  AnalyticsRequest,
  AnalyticsQueryParams 
} from '../types';
import { logger } from '../utils/logger';

export class AnalyticsService {
  private engagementData: Map<string, EngagementMetrics> = new Map();

  async getEngagementMetrics(request: AnalyticsQueryParams): Promise<{
    totalSessions: number;
    totalMessages: number;
    totalQuizzes: number;
    averageSessionDuration: number;
    engagementMetrics: EngagementMetrics[];
  }> {
    try {
      let metrics = Array.from(this.engagementData.values());

      // Filter by request parameters
      if (request.userId) {
        metrics = metrics.filter(m => m.userId === request.userId);
      }
      
      if (request.sessionId) {
        metrics = metrics.filter(m => m.sessionId === request.sessionId);
      }

      if (request.startDate) {
        const startDate = new Date(request.startDate);
        metrics = metrics.filter(m => new Date(m.lastActivity) >= startDate);
      }

      if (request.endDate) {
        const endDate = new Date(request.endDate);
        metrics = metrics.filter(m => new Date(m.lastActivity) <= endDate);
      }

      // Calculate aggregated metrics
      const totalSessions = metrics.length;
      const totalMessages = metrics.reduce((sum, m) => sum + m.messagesPerSession, 0);
      const totalQuizzes = metrics.reduce((sum, m) => sum + m.quizzesAttempted, 0);
      const averageSessionDuration = totalSessions > 0 
        ? metrics.reduce((sum, m) => sum + m.sessionDuration, 0) / totalSessions 
        : 0;

      return {
        totalSessions,
        totalMessages,
        totalQuizzes,
        averageSessionDuration,
        engagementMetrics: metrics
      };

    } catch (error) {
      logger.error('Failed to get engagement metrics:', error);
      throw error;
    }
  }

  async getSessionMetrics(sessionId: string): Promise<EngagementMetrics | null> {
    try {
      return this.engagementData.get(sessionId) || null;
    } catch (error) {
      logger.error('Failed to get session metrics:', error);
      throw error;
    }
  }

  async getUserMetrics(userId: string): Promise<EngagementMetrics[]> {
    try {
      const userMetrics = Array.from(this.engagementData.values())
        .filter(m => m.userId === userId);
      
      return userMetrics;
    } catch (error) {
      logger.error('Failed to get user metrics:', error);
      throw error;
    }
  }

  async recordEngagementMetric(metric: EngagementMetrics): Promise<void> {
    try {
      this.engagementData.set(metric.sessionId, metric);
      
      logger.info('Engagement metric recorded', {
        userId: metric.userId,
        sessionId: metric.sessionId,
        messagesPerSession: metric.messagesPerSession,
        quizzesAttempted: metric.quizzesAttempted
      });

      // TODO: Persist to database if configured
      // TODO: Log to Google Sheets via GoogleSheetsService

    } catch (error) {
      logger.error('Failed to record engagement metric:', error);
      throw error;
    }
  }

  async updateSessionMetrics(
    sessionId: string, 
    updates: Partial<EngagementMetrics>
  ): Promise<void> {
    try {
      const existing = this.engagementData.get(sessionId);
      if (existing) {
        const updated = { ...existing, ...updates, lastActivity: new Date().toISOString() };
        this.engagementData.set(sessionId, updated);
        
        logger.debug('Session metrics updated', {
          sessionId,
          updates
        });
      }
    } catch (error) {
      logger.error('Failed to update session metrics:', error);
      throw error;
    }
  }

  async getTopPerformingUsers(limit: number = 10): Promise<{
    userId: string;
    totalSessions: number;
    totalMessages: number;
    totalQuizzes: number;
    averageSessionDuration: number;
  }[]> {
    try {
      const userStats = new Map<string, {
        totalSessions: number;
        totalMessages: number;
        totalQuizzes: number;
        totalDuration: number;
      }>();

      // Aggregate stats by user
      for (const metric of this.engagementData.values()) {
        const existing = userStats.get(metric.userId) || {
          totalSessions: 0,
          totalMessages: 0,
          totalQuizzes: 0,
          totalDuration: 0
        };

        existing.totalSessions++;
        existing.totalMessages += metric.messagesPerSession;
        existing.totalQuizzes += metric.quizzesAttempted;
        existing.totalDuration += metric.sessionDuration;

        userStats.set(metric.userId, existing);
      }

      // Convert to array and sort by total engagement score
      const results = Array.from(userStats.entries())
        .map(([userId, stats]) => ({
          userId,
          totalSessions: stats.totalSessions,
          totalMessages: stats.totalMessages,
          totalQuizzes: stats.totalQuizzes,
          averageSessionDuration: stats.totalDuration / stats.totalSessions
        }))
        .sort((a, b) => {
          // Sort by engagement score (messages + quizzes * 2)
          const scoreA = a.totalMessages + (a.totalQuizzes * 2);
          const scoreB = b.totalMessages + (b.totalQuizzes * 2);
          return scoreB - scoreA;
        })
        .slice(0, limit);

      return results;

    } catch (error) {
      logger.error('Failed to get top performing users:', error);
      throw error;
    }
  }

  async getQuizPerformanceStats(): Promise<{
    totalQuizzes: number;
    averageCorrectRate: number;
    topicBreakdown: Record<string, { attempted: number; correct: number; }>;
  }> {
    try {
      // TODO: This would require integrating with quiz response data
      // For now, return placeholder data
      return {
        totalQuizzes: 0,
        averageCorrectRate: 0,
        topicBreakdown: {}
      };
    } catch (error) {
      logger.error('Failed to get quiz performance stats:', error);
      throw error;
    }
  }

  async cleanupOldSessions(maxAge: number = 7 * 24 * 60 * 60 * 1000): Promise<number> {
    try {
      const cutoffDate = new Date(Date.now() - maxAge);
      let removedCount = 0;

      for (const [sessionId, metric] of this.engagementData.entries()) {
        if (new Date(metric.lastActivity) < cutoffDate) {
          this.engagementData.delete(sessionId);
          removedCount++;
        }
      }

      logger.info(`Cleaned up ${removedCount} old sessions`);
      return removedCount;

    } catch (error) {
      logger.error('Failed to cleanup old sessions:', error);
      throw error;
    }
  }
} 