import { google } from 'googleapis';
import { QuizLogRequest } from '../types';
import { logger } from '../utils/logger';
import path from 'path';

export class GoogleSheetsService {
  private sheets: any = null;
  private spreadsheetId: string;
  private isEnabled: boolean = false;

  constructor() {
    this.spreadsheetId = process.env.GOOGLE_SHEET_ID || '';
    // Don't initialize immediately - wait for first use
  }

  private async ensureInitialized() {
    if (!this.isEnabled && !this.sheets) {
      await this.initializeSheets();
    }
  }

  private async initializeSheets() {
    try {
      // Re-read environment variables in case they weren't available during construction
      const credentialsPath = process.env.GOOGLE_APPLICATION_CREDENTIALS;
      this.spreadsheetId = process.env.GOOGLE_SHEET_ID || '';
      
      logger.info('Google Sheets initialization debug', {
        credentialsPath,
        spreadsheetId: this.spreadsheetId,
        hasCredentials: !!credentialsPath,
        hasSpreadsheetId: !!this.spreadsheetId,
        allEnvVars: {
          GOOGLE_SHEET_ID: process.env.GOOGLE_SHEET_ID,
          GOOGLE_APPLICATION_CREDENTIALS: process.env.GOOGLE_APPLICATION_CREDENTIALS
        }
      });
      
      if (!credentialsPath || !this.spreadsheetId) {
        logger.warn('Google Sheets credentials or spreadsheet ID not configured', {
          credentialsPath,
          spreadsheetId: this.spreadsheetId
        });
        return;
      }

      // Resolve the credentials path relative to the project root
      const fullCredentialsPath = path.resolve(process.cwd(), credentialsPath);
      
      const auth = new google.auth.GoogleAuth({
        keyFile: fullCredentialsPath,
        scopes: ['https://www.googleapis.com/auth/spreadsheets']
      });

      this.sheets = google.sheets({ version: 'v4', auth });
      this.isEnabled = true;
      
      logger.info('Google Sheets service initialized successfully', {
        spreadsheetId: this.spreadsheetId
      });

      // Ensure the spreadsheet has the proper structure
      await this.ensureSpreadsheetStructure();

    } catch (error) {
      logger.error('Failed to initialize Google Sheets:', error);
      this.isEnabled = false;
    }
  }

  async logQuizResponse(response: QuizLogRequest): Promise<void> {
    await this.ensureInitialized();
    
    if (!this.isEnabled || !this.sheets || !this.spreadsheetId) {
      logger.info('Google Sheets not configured, logging quiz response locally', {
        userId: response.userId,
        quizId: response.quizId,
        correct: response.correct,
        topicTag: response.topicTag
      });
      return;
    }

    try {
      const values = [
        [
          response.userId,
          response.timestamp,
          response.quizId,
          response.topicTag,
          response.selectedOption,
          response.correct,
          response.sessionId
        ]
      ];

      await this.sheets.spreadsheets.values.append({
        spreadsheetId: this.spreadsheetId,
        range: 'QuizResponses!A:G',
        valueInputOption: 'RAW',
        insertDataOption: 'INSERT_ROWS',
        resource: {
          values
        }
      });

      logger.info('Quiz response logged to Google Sheets', {
        userId: response.userId,
        quizId: response.quizId
      });

    } catch (error) {
      logger.error('Failed to log quiz response to Google Sheets:', error);
      // Don't throw error to prevent breaking the quiz flow
    }
  }

  async logEngagementMetrics(metrics: any): Promise<void> {
    await this.ensureInitialized();
    
    if (!this.isEnabled || !this.sheets || !this.spreadsheetId) {
      logger.info('Google Sheets not configured, logging engagement metrics locally', {
        userId: metrics.userId,
        sessionId: metrics.sessionId,
        messagesPerSession: metrics.messagesPerSession
      });
      return;
    }

    try {
      const values = [
        [
          metrics.userId,
          metrics.sessionId,
          metrics.messagesPerSession,
          metrics.sessionDuration,
          metrics.quizzesAttempted,
          metrics.preTestCompleted,
          metrics.lastActivity,
          metrics.confidenceRating || ''
        ]
      ];

      await this.sheets.spreadsheets.values.append({
        spreadsheetId: this.spreadsheetId,
        range: 'EngagementLogs!A:H',
        valueInputOption: 'RAW',
        insertDataOption: 'INSERT_ROWS',
        resource: {
          values
        }
      });

      logger.info('Engagement metrics logged to Google Sheets', {
        userId: metrics.userId,
        sessionId: metrics.sessionId
      });

    } catch (error) {
      logger.error('Failed to log engagement metrics to Google Sheets:', error);
      // Don't throw error to prevent breaking the application flow
    }
  }

  async logChatMessage(messageData: {
    userId: string;
    sessionId: string;
    message: string;
    response: string;
    timestamp: string;
    messageType: 'user' | 'assistant' | 'system';
  }): Promise<void> {
    await this.ensureInitialized();
    
    if (!this.isEnabled || !this.sheets || !this.spreadsheetId) {
      logger.info('Google Sheets not configured, logging chat message locally', {
        userId: messageData.userId,
        sessionId: messageData.sessionId
      });
      return;
    }

    try {
      const values = [
        [
          messageData.userId,
          messageData.sessionId,
          messageData.timestamp,
          messageData.messageType,
          messageData.message,
          messageData.response
        ]
      ];

      await this.sheets.spreadsheets.values.append({
        spreadsheetId: this.spreadsheetId,
        range: 'ChatLogs!A:F',
        valueInputOption: 'RAW',
        insertDataOption: 'INSERT_ROWS',
        resource: {
          values
        }
      });

      logger.info('Chat message logged to Google Sheets', {
        userId: messageData.userId,
        sessionId: messageData.sessionId
      });

    } catch (error) {
      logger.error('Failed to log chat message to Google Sheets:', error);
      // Don't throw error to prevent breaking the chat flow
    }
  }

  async logCourseProgress(progressData: {
    userId: string;
    sessionId: string;
    courseId: string;
    courseName: string;
    pageNumber: number;
    totalPages: number;
    completed: boolean;
    timestamp: string;
  }): Promise<void> {
    await this.ensureInitialized();
    
    if (!this.isEnabled || !this.sheets || !this.spreadsheetId) {
      logger.info('Google Sheets not configured, logging course progress locally', progressData);
      return;
    }

    try {
      const values = [
        [
          progressData.userId,
          progressData.sessionId,
          progressData.courseId,
          progressData.courseName,
          progressData.pageNumber,
          progressData.totalPages,
          progressData.completed,
          progressData.timestamp
        ]
      ];

      await this.sheets.spreadsheets.values.append({
        spreadsheetId: this.spreadsheetId,
        range: 'CourseProgress!A:H',
        valueInputOption: 'RAW',
        insertDataOption: 'INSERT_ROWS',
        resource: {
          values
        }
      });

      logger.info('Course progress logged to Google Sheets', {
        userId: progressData.userId,
        courseId: progressData.courseId
      });

    } catch (error) {
      logger.error('Failed to log course progress to Google Sheets:', error);
      // Don't throw error to prevent breaking the course flow
    }
  }

  private async ensureSpreadsheetStructure(): Promise<void> {
    if (!this.isEnabled || !this.sheets) {
      return;
    }

    try {
      // Get current spreadsheet info
      const spreadsheet = await this.sheets.spreadsheets.get({
        spreadsheetId: this.spreadsheetId
      });

      const existingSheets = spreadsheet.data.sheets.map((sheet: any) => sheet.properties.title);
      const requiredSheets = ['QuizResponses', 'EngagementLogs', 'ChatLogs', 'CourseProgress'];

      // Create missing sheets
      for (const sheetName of requiredSheets) {
        if (!existingSheets.includes(sheetName)) {
          await this.sheets.spreadsheets.batchUpdate({
            spreadsheetId: this.spreadsheetId,
            resource: {
              requests: [
                {
                  addSheet: {
                    properties: {
                      title: sheetName
                    }
                  }
                }
              ]
            }
          });
          logger.info(`Created sheet: ${sheetName}`);
        }
      }

      // Add headers to sheets
      await this.addHeaders();

    } catch (error) {
      logger.error('Failed to ensure spreadsheet structure:', error);
    }
  }

  private async addHeaders(): Promise<void> {
    if (!this.isEnabled || !this.sheets) {
      return;
    }

    try {
      const headerUpdates = [
        {
          range: 'QuizResponses!A1:G1',
          values: [['user_id', 'timestamp', 'quiz_id', 'topic_tag', 'selected_option', 'correct', 'session_id']]
        },
        {
          range: 'EngagementLogs!A1:H1',
          values: [['user_id', 'session_id', 'messages_per_session', 'session_duration', 'quizzes_attempted', 'pretest_completed', 'last_activity', 'confidence_rating']]
        },
        {
          range: 'ChatLogs!A1:F1',
          values: [['user_id', 'session_id', 'timestamp', 'message_type', 'message', 'response']]
        },
        {
          range: 'CourseProgress!A1:H1',
          values: [['user_id', 'session_id', 'course_id', 'course_name', 'page_number', 'total_pages', 'completed', 'timestamp']]
        }
      ];

      for (const update of headerUpdates) {
        try {
          await this.sheets.spreadsheets.values.update({
            spreadsheetId: this.spreadsheetId,
            range: update.range,
            valueInputOption: 'RAW',
            resource: {
              values: update.values
            }
          });
        } catch (error) {
          // Headers might already exist, continue with other updates
          logger.debug(`Header update failed for ${update.range}:`, error);
        }
      }

      logger.info('Headers updated in Google Sheets');

    } catch (error) {
      logger.error('Failed to add headers to Google Sheets:', error);
    }
  }

  // Utility method to check if the service is working
  async testConnection(): Promise<boolean> {
    await this.ensureInitialized();
    
    if (!this.isEnabled || !this.sheets || !this.spreadsheetId) {
      return false;
    }

    try {
      await this.sheets.spreadsheets.get({
        spreadsheetId: this.spreadsheetId
      });
      return true;
    } catch (error) {
      logger.error('Google Sheets connection test failed:', error);
      return false;
    }
  }

  // Get service status
  getStatus(): { enabled: boolean; spreadsheetId: string } {
    return {
      enabled: this.isEnabled,
      spreadsheetId: this.spreadsheetId
    };
  }
} 