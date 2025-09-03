import { Router } from "express";
import { ContentController } from '../controllers/contentController';
import { asyncHandler } from '../middleware/errorHandler';

const router = Router();
const contentController = new ContentController();

// Configure multer middleware
const upload = contentController.getUploadMiddleware();

// POST /api/content/upload - Handle file upload
router.post('/upload', upload.single('file'), asyncHandler(contentController.uploadFile.bind(contentController)));

// POST /api/content/remove - Remove uploaded content
router.post('/remove', asyncHandler(contentController.removeFile.bind(contentController)));

// GET /api/content/list - List user's uploaded files
router.get('/list', asyncHandler(contentController.listFiles.bind(contentController)));

// Export function to get user content (used by other services)
export function getUserContent(userId: string, sessionId: string): string[] {
  return contentController.getUserContent(userId, sessionId);
}

export { router as contentRouter };
 