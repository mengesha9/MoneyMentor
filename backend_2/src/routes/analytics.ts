import { Router } from 'express';
import { AnalyticsController } from '../controllers/analyticsController';
import { asyncHandler } from '../middleware/errorHandler';

const router = Router();
const analyticsController = new AnalyticsController();

// GET /api/analytics - Get engagement metrics
router.get('/', asyncHandler(analyticsController.getEngagementMetrics.bind(analyticsController)));

// GET /api/analytics/session/:sessionId - Get session-specific metrics
router.get('/session/:sessionId', asyncHandler(analyticsController.getSessionMetrics.bind(analyticsController)));

// GET /api/analytics/user/:userId - Get user-specific metrics
router.get('/user/:userId', asyncHandler(analyticsController.getUserMetrics.bind(analyticsController)));

export { router as analyticsRouter }; 