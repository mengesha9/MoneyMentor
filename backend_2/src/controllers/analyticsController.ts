import { Request, Response } from 'express';
import { 
  AnalyticsQueryParams,
  AnalyticsResponse 
} from '../types';
import { AnalyticsService } from '../services/analyticsService';
import { logger } from '../utils/logger';

export class AnalyticsController {
  private analyticsService: AnalyticsService;

  constructor() {
    this.analyticsService = new AnalyticsService();
  }

  // GET /api/analytics - Get engagement metrics
  async getEngagementMetrics(req: Request, res: Response): Promise<void> {
    const { userId, sessionId, startDate, endDate }: AnalyticsQueryParams = req.query as any;

    try {
      const analytics = await this.analyticsService.getEngagementMetrics({
        userId,
        sessionId,
        startDate,
        endDate
      });

      const response: AnalyticsResponse = {
        success: true,
        data: analytics
      };

      logger.info('Analytics retrieved', {
        userId,
        sessionId,
        dateRange: { startDate, endDate }
      });

      res.json(response);

    } catch (error) {
      logger.error('Analytics retrieval error:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to retrieve analytics'
      });
    }
  }

  // GET /api/analytics/session/:sessionId - Get session-specific metrics
  async getSessionMetrics(req: Request, res: Response): Promise<void> {
    const { sessionId } = req.params;

    if (!sessionId || typeof sessionId !== 'string') {
      res.status(400).json({
        success: false,
        error: 'Invalid session ID'
      });
      return;
    }

    try {
      const sessionMetrics = await this.analyticsService.getSessionMetrics(sessionId);
      
      res.json({
        success: true,
        data: sessionMetrics
      });

    } catch (error) {
      logger.error('Session metrics retrieval error:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to retrieve session metrics'
      });
    }
  }

  // GET /api/analytics/user/:userId - Get user-specific metrics
  async getUserMetrics(req: Request, res: Response): Promise<void> {
    const { userId } = req.params;

    if (!userId || typeof userId !== 'string') {
      res.status(400).json({
        success: false,
        error: 'Invalid user ID'
      });
      return;
    }

    try {
      const userMetrics = await this.analyticsService.getUserMetrics(userId);
      
      res.json({
        success: true,
        data: userMetrics
      });

    } catch (error) {
      logger.error('User metrics retrieval error:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to retrieve user metrics'
      });
    }
  }
}
