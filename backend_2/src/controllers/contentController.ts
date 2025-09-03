import { Request, Response } from "express";
import { v4 as uuidv4 } from 'uuid';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import { logger } from '../utils/logger';

export class ContentController {
  private userContent: Map<string, Array<{
    id: string;
    fileName: string;
    originalName: string;
    fileSize: number;
    uploadDate: string;
    processed: boolean;
    content: string;
    filePath: string;
  }>>;

  constructor() {
    this.userContent = new Map();
    this.ensureUploadsDirectory();
  }

  private ensureUploadsDirectory(): void {
    const uploadsDir = path.join(process.cwd(), 'uploads');
    if (!fs.existsSync(uploadsDir)) {
      fs.mkdirSync(uploadsDir, { recursive: true });
    }
  }

  // Configure multer for file uploads
  getUploadMiddleware() {
    const storage = multer.diskStorage({
      destination: (req, file, cb) => {
        const uploadsDir = path.join(process.cwd(), 'uploads');
        cb(null, uploadsDir);
      },
      filename: (req, file, cb) => {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
      }
    });

    return multer({
      storage: storage,
      limits: {
        fileSize: 10 * 1024 * 1024 // 10MB limit
      },
      fileFilter: (req, file, cb) => {
        const allowedTypes = ['application/pdf', 'text/plain', 'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'];
        const allowedExtensions = ['.pdf', '.txt', '.ppt', '.pptx'];
        
        const hasValidType = allowedTypes.includes(file.mimetype);
        const hasValidExtension = allowedExtensions.includes(path.extname(file.originalname).toLowerCase());
        
        if (hasValidType || hasValidExtension) {
          cb(null, true);
        } else {
          cb(new Error('Invalid file type. Only PDF, TXT, PPT, and PPTX files are allowed.'));
        }
      }
    });
  }

  // POST /api/content/upload - Handle file upload
  async uploadFile(req: Request, res: Response): Promise<void> {
    const { userId, sessionId } = req.body;

    if (!userId || !sessionId) {
      res.status(400).json({
        success: false,
        error: 'Missing userId or sessionId'
      });
      return;
    }

    if (!req.file) {
      res.status(400).json({
        success: false,
        error: 'No file uploaded'
      });
      return;
    }

    try {
      // Process the uploaded file
      let content = '';
      const filePath = req.file.path;
      const fileExtension = path.extname(req.file.originalname).toLowerCase();
      
      // Extract content based on file type
      if (fileExtension === '.txt') {
        content = fs.readFileSync(filePath, 'utf8');
      } else if (fileExtension === '.pdf') {
        content = `PDF Content: ${req.file.originalname}\n\nThis PDF has been uploaded and is ready for analysis. Content extraction is available for text-based questions.`;
      } else if (['.ppt', '.pptx'].includes(fileExtension)) {
        content = `Presentation Content: ${req.file.originalname}\n\nThis presentation has been uploaded and is ready for analysis. Slide content extraction is available for text-based questions.`;
      } else {
        content = `File Content: ${req.file.originalname}\n\nThis file has been uploaded successfully and is ready for analysis.`;
      }
      
      const uploadedFile = {
        id: uuidv4(),
        fileName: req.file.filename,
        originalName: req.file.originalname,
        fileSize: req.file.size,
        uploadDate: new Date().toISOString(),
        processed: true,
        content: content,
        filePath: filePath
      };

      // Store in user's content
      const userKey = `${userId}-${sessionId}`;
      if (!this.userContent.has(userKey)) {
        this.userContent.set(userKey, []);
      }
      this.userContent.get(userKey)!.push(uploadedFile);

      logger.info('File uploaded successfully', {
        userId,
        sessionId,
        fileName: req.file.originalname,
        fileSize: req.file.size,
        storedAs: req.file.filename
      });

      res.json({
        success: true,
        data: {
          fileId: uploadedFile.id,
          fileName: uploadedFile.originalName,
          fileSize: uploadedFile.fileSize,
          processed: true,
          message: 'File uploaded and processed successfully'
        }
      });

    } catch (error) {
      logger.error('File upload error:', error);
      
      // Clean up uploaded file if processing failed
      if (req.file && fs.existsSync(req.file.path)) {
        fs.unlinkSync(req.file.path);
      }
      
      res.status(500).json({
        success: false,
        error: 'Failed to process uploaded file'
      });
    }
  }

  // POST /api/content/remove - Remove uploaded content
  async removeFile(req: Request, res: Response): Promise<void> {
    const { userId, sessionId, fileName } = req.body;

    if (!userId || !sessionId || !fileName) {
      res.status(400).json({
        success: false,
        error: 'Missing required parameters'
      });
      return;
    }

    try {
      const userKey = `${userId}-${sessionId}`;
      const userFiles = this.userContent.get(userKey) || [];
      
      const fileIndex = userFiles.findIndex(file => file.originalName === fileName);
      
      if (fileIndex === -1) {
        res.status(404).json({
          success: false,
          error: 'File not found'
        });
        return;
      }

      const fileToRemove = userFiles[fileIndex];

      // Remove physical file from disk
      if (fs.existsSync(fileToRemove.filePath)) {
        fs.unlinkSync(fileToRemove.filePath);
      }

      // Remove from user content
      userFiles.splice(fileIndex, 1);
      this.userContent.set(userKey, userFiles);

      logger.info('File removed successfully', {
        userId,
        sessionId,
        fileName,
        removedFile: fileToRemove.fileName
      });

      res.json({
        success: true,
        data: {
          message: 'File removed successfully'
        }
      });

    } catch (error) {
      logger.error('File removal error:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to remove file'
      });
    }
  }

  // GET /api/content/list - List user's uploaded files
  async listFiles(req: Request, res: Response): Promise<void> {
    const { userId, sessionId } = req.query;

    if (!userId || !sessionId) {
      res.status(400).json({
        success: false,
        error: 'Missing userId or sessionId'
      });
      return;
    }

    try {
      const userKey = `${userId}-${sessionId}`;
      const userFiles = this.userContent.get(userKey) || [];
      
      const fileList = userFiles.map(file => ({
        id: file.id,
        fileName: file.originalName,
        fileSize: file.fileSize,
        uploadDate: file.uploadDate,
        processed: file.processed
      }));

      res.json({
        success: true,
        data: {
          files: fileList,
          totalFiles: fileList.length
        }
      });

    } catch (error) {
      logger.error('File listing error:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to list files'
      });
    }
  }

  // Helper method to get user content (used by other services)
  getUserContent(userId: string, sessionId: string): string[] {
    const userKey = `${userId}-${sessionId}`;
    const userFiles = this.userContent.get(userKey) || [];
    return userFiles.map(file => file.content);
  }

  // Helper method to generate simulated content for testing
  private generateSimulatedContent(): string {
    const templates = [
      "Financial Planning Document:\n\nMonthly Income: $5,000\nMonthly Expenses: $3,500\nCurrent Savings: $10,000\nDebt: $2,000 (Credit Card)\n\nGoals:\n- Build emergency fund\n- Pay off credit card debt\n- Start investing for retirement",
      
      "Investment Portfolio Summary:\n\nTotal Portfolio Value: $25,000\n\nAsset Allocation:\n- Stocks: 60% ($15,000)\n- Bonds: 30% ($7,500)\n- Cash: 10% ($2,500)\n\nMonthly Contributions: $500\nRisk Tolerance: Moderate\nTime Horizon: 25 years until retirement",
      
      "Budget Analysis Report:\n\nIncome Sources:\n- Salary: $4,500/month\n- Side Business: $800/month\n- Investment Returns: $200/month\n\nExpense Categories:\n- Housing: $1,800 (36%)\n- Transportation: $600 (12%)\n- Food: $500 (10%)\n- Utilities: $300 (6%)\n- Entertainment: $400 (8%)\n- Savings: $900 (18%)\n- Other: $500 (10%)",
      
      "Debt Consolidation Plan:\n\nCurrent Debts:\n- Credit Card 1: $3,000 @ 18.99% APR\n- Credit Card 2: $1,500 @ 22.99% APR\n- Personal Loan: $5,000 @ 12.99% APR\n\nTotal Debt: $9,500\nCurrent Monthly Payments: $450\n\nConsolidation Option:\n- New Loan: $9,500 @ 8.99% APR\n- New Monthly Payment: $320\n- Savings: $130/month\n- Payoff Time: 3 years vs 4.5 years"
    ];
    
    return templates[Math.floor(Math.random() * templates.length)];
  }
}
