import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import json
import asyncio
from pathlib import Path
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    """Service for interacting with Google Sheets for comprehensive logging
    
    Sheet schemas:
    - QuizResponses: user_id | timestamp | quiz_id | topic_tag | selected_option | correct | session_id
    - EngagementLogs: user_id | session_id | messages_per_session | session_duration | quizzes_attempted | pretest_completed | last_activity | confidence_rating
    - ChatLogs: user_id | session_id | timestamp | message_type | message | response
    - CourseProgress: user_id | session_id | course_id | course_name | page_number | total_pages | completed | timestamp
    """
    
    def __init__(self):
        self.service = None
        self.drive_service = None
        # Use the correct environment variable name from config
        self.spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID') or os.getenv('GOOGLE_SHEET_ID')
        self.client_email = os.getenv('GOOGLE_CLIENT_EMAIL')  # Client's email for access
        self._init_service()
    
    def _init_service(self):
        """Initialize Google Sheets and Drive services with service account credentials"""
        try:
            # Get the path to the service account JSON file
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if not credentials_path:
                logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set")
                return
            
            # Resolve the path relative to the backend directory
            backend_dir = Path(__file__).resolve().parent.parent.parent
            credentials_file = backend_dir / credentials_path
            
            if not credentials_file.exists():
                logger.error(f"Service account credentials file not found: {credentials_file}")
                return
            
            # Load credentials from file
            with open(credentials_file, 'r') as f:
                credentials_dict = json.load(f)
            
            # Create credentials with required scopes
            credentials = Credentials.from_service_account_info(
                credentials_dict,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
            )
            
            # Build services with proper configuration
            self.service = build('sheets', 'v4', credentials=credentials)
            self.drive_service = build('drive', 'v3', credentials=credentials)
            logger.info("Google Sheets and Drive services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets service: {e}")
            self.service = None
            self.drive_service = None
    
    def setup_client_access(self) -> bool:
        """
        Set up client access to the Google Sheet
        
        This method:
        1. Creates the sheet if it doesn't exist
        2. Sets up all required tabs with headers
        3. Shares the sheet with the client's email (read-only)
        4. Creates optional tabs (ConfidencePolls, UsageLogs)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.service or not self.drive_service:
                logger.error("Google services not initialized")
                return False
            
            if not self.spreadsheet_id:
                logger.error("Spreadsheet ID not configured. Set GOOGLE_SHEETS_SPREADSHEET_ID in your .env file")
                return False
            
            if not self.client_email:
                logger.error("Client email not configured")
                return False
            
            # 1. Check if sheet exists and create if needed
            try:
                sheet_info = self.service.spreadsheets().get(
                    spreadsheetId=self.spreadsheet_id
                ).execute()
                logger.info(f"Sheet exists: {sheet_info.get('properties', {}).get('title', 'Unknown')}")
            except HttpError as e:
                if e.resp.status == 404:
                    logger.error("Spreadsheet not found. Please create it and share with service account.")
                    return False
                else:
                    raise e
            
            # 2. Set up all required tabs with headers
            sheet_configs = {
                'QuizResponses': ['user_id', 'timestamp', 'quiz_id', 'topic_tag', 'selected_option', 'correct', 'session_id'],
                'EngagementLogs': ['user_id', 'session_id', 'messages_per_session', 'session_duration', 'quizzes_attempted', 'pretest_completed', 'last_activity', 'confidence_rating'],
                'ChatLogs': ['user_id', 'session_id', 'timestamp', 'message_type', 'message', 'response'],
                'CourseProgress': ['user_id', 'session_id', 'course_id', 'course_name', 'page_number', 'total_pages', 'completed', 'timestamp'],
                'UserProfiles': ['first_name', 'last_name', 'email', 'total_chats', 'quizzes_taken', 'day_streak', 'days_active', 'courses_enrolled', 'total_course_score', 'courses_completed', 'course_details']
            }
            
            for sheet_name, headers in sheet_configs.items():
                self._setup_sheet_tab(sheet_name, headers)
            
            # 3. Share with client email (read-only)
            self._share_with_client()
            
            logger.info("Client access setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup client access: {e}")
            return False
    
    def _setup_sheet_tab(self, sheet_name: str, headers: List[str]):
        """Create a sheet tab with the given name and headers"""
        try:
            # Check if tab exists
            self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{sheet_name}!A1:A1'
            ).execute()
            logger.info(f"Tab {sheet_name} already exists")
            
        except HttpError as e:
            if e.resp.status == 400:
                # Tab doesn't exist, create it
                add_sheet_request = {
                    'addSheet': {
                        'properties': {
                            'title': sheet_name,
                            'gridProperties': {
                                'rowCount': 1000,
                                'columnCount': len(headers)
                            }
                        }
                    }
                }
                
                body = {
                    'requests': [add_sheet_request]
                }
                
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=body
                ).execute()
                
                logger.info(f"Tab {sheet_name} created with headers")
            else:
                raise e
        
        # Add headers if they don't exist
        try:
            existing_headers = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{sheet_name}!A1:{chr(65 + len(headers) - 1)}1'
            ).execute()
            
            if not existing_headers.get('values'):
                # Set up headers
                header_body = {
                    'values': [headers]
                }
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'{sheet_name}!A1:{chr(65 + len(headers) - 1)}1',
                    valueInputOption='RAW',
                    body=header_body
                ).execute()
                logger.info(f"{sheet_name} headers set up successfully")
            else:
                logger.info(f"{sheet_name} headers already exist")
                
        except Exception as e:
            logger.error(f"Failed to set up headers for {sheet_name}: {e}")
            raise e
    
    def _share_with_client(self):
        """Share the spreadsheet with the client email (read-only)"""
        try:
            # Check if already shared
            permissions = self.drive_service.permissions().list(
                fileId=self.spreadsheet_id
            ).execute()
            
            client_shared = any(
                perm.get('emailAddress') == self.client_email 
                for perm in permissions.get('permissions', [])
            )
            
            if not client_shared:
                # Share with client (read-only) with improved notification
                permission = {
                    'type': 'user',
                    'role': 'reader',
                    'emailAddress': self.client_email
                }
                
                # Create a professional email message to reduce spam filtering
                email_message = f"""
Hello,

You have been granted access to the MoneyMentor AI Chatbot Analytics spreadsheet.

Spreadsheet Details:
- Title: MoneyMentor Analytics
- Purpose: Track user interactions, quiz responses, and course progress
- Access Level: Read-only
- Contains: QuizResponses, EngagementLogs, ChatLogs, CourseProgress

You can access the spreadsheet at:
https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}

The spreadsheet contains comprehensive analytics data across multiple tabs for monitoring user engagement and learning progress.

This is an automated notification from the MoneyMentor AI Chatbot system.

Best regards,
MoneyMentor Team
                """.strip()
                
                self.drive_service.permissions().create(
                    fileId=self.spreadsheet_id,
                    body=permission,
                    sendNotificationEmail=True,
                    emailMessage=email_message
                ).execute()
                
                logger.info(f"Shared spreadsheet with client: {self.client_email}")
            else:
                logger.info("Spreadsheet already shared with client")
                
        except Exception as e:
            logger.error(f"Failed to share with client: {e}")
            raise e
    
    def log_quiz_response(self, quiz_data: Dict[str, Any]) -> bool:
        """
        Log a quiz response to Google Sheets QuizResponses tab
        
        Args:
            quiz_data: Dictionary containing:
                - user_id: str
                - quiz_id: str
                - topic_tag: str
                - selected_option: str (A, B, C, or D)
                - correct: bool
                - session_id: str
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.service or not self.spreadsheet_id:
                logger.warning("Google Sheets service not available")
                return False
            
            # Prepare data row according to schema
            # Schema: user_id | timestamp | quiz_id | topic_tag | selected_option | correct | session_id
            row_data = [
                quiz_data.get('user_id', ''),
                datetime.utcnow().isoformat(),  # timestamp
                quiz_data.get('quiz_id', ''),
                quiz_data.get('topic_tag', ''),
                quiz_data.get('selected_option', ''),  # A, B, C, or D
                'TRUE' if quiz_data.get('correct', False) else 'FALSE',
                quiz_data.get('session_id', '')
            ]
            
            # Append to QuizResponses tab with timeout handling
            body = {
                'values': [row_data]
            }
            
            # Set socket timeout for this request
            import socket
            original_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(15.0)  # 15 second timeout
            
            try:
                result = self.service.spreadsheets().values().append(
                    spreadsheetId=self.spreadsheet_id,
                    range='QuizResponses!A:G',
                    valueInputOption='RAW',
                    insertDataOption='INSERT_ROWS',
                    body=body
                ).execute()
                
                logger.info(f"Quiz response logged to Google Sheets: {result.get('updates', {}).get('updatedRows', 0)} rows updated")
                return True
                
            finally:
                # Restore original timeout
                socket.setdefaulttimeout(original_timeout)
            
        except HttpError as e:
            logger.error(f"Google Sheets API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to log quiz response to Google Sheets: {e}")
            return False
    
    def log_multiple_responses(self, responses: List[Dict[str, Any]]) -> bool:
        """
        Log multiple quiz responses in a batch
        
        Args:
            responses: List of quiz response dictionaries
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.service or not self.spreadsheet_id:
                logger.warning("Google Sheets service not available")
                return False
            
            # Prepare batch data according to schema
            rows_data = []
            for response in responses:
                row_data = [
                    response.get('user_id', ''),
                    datetime.utcnow().isoformat(),
                    response.get('quiz_id', ''),
                    response.get('topic_tag', ''),
                    response.get('selected_option', ''),  # A, B, C, or D
                    'TRUE' if response.get('correct', False) else 'FALSE',
                    response.get('session_id', '')
                ]
                rows_data.append(row_data)
            
            # Append batch to QuizResponses tab
            body = {
                'values': rows_data
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range='QuizResponses!A:G',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"Batch quiz responses logged to Google Sheets: {result.get('updates', {}).get('updatedRows', 0)} rows updated")
            return True
            
        except HttpError as e:
            logger.error(f"Google Sheets API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to log batch quiz responses to Google Sheets: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test the Google Sheets connection and access to all tabs
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if not self.service or not self.spreadsheet_id:
                return False
            
            # Test access to all required tabs
            required_tabs = ['QuizResponses', 'EngagementLogs', 'ChatLogs', 'CourseProgress', 'UserProfiles']
            
            for tab_name in required_tabs:
                try:
                    result = self.service.spreadsheets().values().get(
                        spreadsheetId=self.spreadsheet_id,
                        range=f'{tab_name}!A1:A1'
                    ).execute()
                    logger.info(f"Successfully accessed {tab_name} tab")
                except Exception as e:
                    logger.error(f"Failed to access {tab_name} tab: {e}")
                    return False
            
            logger.info("Google Sheets connection test successful for all tabs")
            return True
            
        except Exception as e:
            logger.error(f"Google Sheets connection test failed: {e}")
            return False
    
    def get_sheet_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the Google Sheet and access permissions
        
        Returns:
            Dict containing sheet information or None if failed
        """
        try:
            if not self.service or not self.spreadsheet_id:
                return None
            
            # Get sheet info
            result = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            # Get permissions
            permissions_info = None
            if self.drive_service:
                try:
                    permissions = self.drive_service.permissions().list(
                        fileId=self.spreadsheet_id
                    ).execute()
                    permissions_info = [
                        {
                            'email': perm.get('emailAddress'),
                            'role': perm.get('role'),
                            'type': perm.get('type')
                        }
                        for perm in permissions.get('permissions', [])
                    ]
                except Exception as e:
                    logger.warning(f"Could not retrieve permissions: {e}")
            
            return {
                'title': result.get('properties', {}).get('title', ''),
                'sheets': [sheet.get('properties', {}).get('title', '') for sheet in result.get('sheets', [])],
                'spreadsheet_id': self.spreadsheet_id,
                'client_email': self.client_email,
                'permissions': permissions_info
            }
            
        except Exception as e:
            logger.error(f"Failed to get sheet info: {e}")
            return None
    
    async def log_engagement(self, engagement_data: Dict[str, Any]) -> bool:
        """
        Log engagement data to Google Sheets EngagementLogs tab
        
        Args:
            engagement_data: Dictionary containing:
                - user_id: str
                - session_id: str
                - messages_per_session: int
                - session_duration: float (in seconds)
                - quizzes_attempted: int
                - pretest_completed: bool
                - last_activity: str (timestamp)
                - confidence_rating: int (optional)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.service or not self.spreadsheet_id:
                logger.warning("Google Sheets service not available")
                return False
            
            # Prepare data row according to schema
            # Schema: user_id | session_id | messages_per_session | session_duration | quizzes_attempted | pretest_completed | last_activity | confidence_rating
            row_data = [
                engagement_data.get('user_id', ''),
                engagement_data.get('session_id', ''),
                str(engagement_data.get('messages_per_session', 0)),
                str(engagement_data.get('session_duration', 0)),
                str(engagement_data.get('quizzes_attempted', 0)),
                'TRUE' if engagement_data.get('pretest_completed', False) else 'FALSE',
                engagement_data.get('last_activity', datetime.utcnow().isoformat()),
                str(engagement_data.get('confidence_rating', ''))
            ]
            
            # Append to EngagementLogs tab with async timeout
            body = {
                'values': [row_data]
            }
            
            # Use asyncio timeout for the API call
            try:
                # Create a coroutine that wraps the sync API call
                def make_api_call():
                    return self.service.spreadsheets().values().append(
                        spreadsheetId=self.spreadsheet_id,
                        range='EngagementLogs!A:H',
                        valueInputOption='RAW',
                        insertDataOption='INSERT_ROWS',
                        body=body
                    ).execute()
                
                # Run the API call with timeout
                result = await asyncio.wait_for(
                    asyncio.to_thread(make_api_call),
                    timeout=2.0  # Reduced from 10.0 to 2.0 seconds
                )
                
                logger.info(f"Engagement data logged to Google Sheets: {result.get('updates', {}).get('updatedRows', 0)} rows updated")
                return True
                
            except asyncio.TimeoutError:
                logger.error("Google Sheets API call timed out after 2 seconds")
                return False
            except Exception as api_error:
                logger.error(f"Google Sheets API error: {api_error}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to log engagement data to Google Sheets: {e}")
            return False
    
    async def log_chat_message(self, chat_data: Dict[str, Any]) -> bool:
        """
        Log chat message to Google Sheets ChatLogs tab
        
        Args:
            chat_data: Dictionary containing:
                - user_id: str
                - session_id: str
                - message_type: str (user/assistant/system)
                - message: str
                - response: str
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.service or not self.spreadsheet_id:
                logger.warning("Google Sheets service not available")
                return False
            
            # Prepare data row according to schema
            # Schema: user_id | session_id | timestamp | message_type | message | response
            row_data = [
                chat_data.get('user_id', ''),
                chat_data.get('session_id', ''),
                datetime.utcnow().isoformat(),  # timestamp
                chat_data.get('message_type', ''),
                chat_data.get('message', ''),
                chat_data.get('response', '')
            ]
            
            # Append to ChatLogs tab
            body = {
                'values': [row_data]
            }
            
            # Use asyncio timeout for the API call
            try:
                # Create a coroutine that wraps the sync API call
                def make_api_call():
                    return self.service.spreadsheets().values().append(
                        spreadsheetId=self.spreadsheet_id,
                        range='ChatLogs!A:F',
                        valueInputOption='RAW',
                        insertDataOption='INSERT_ROWS',
                        body=body
                    ).execute()
                
                # Run the API call with timeout
                result = await asyncio.wait_for(
                    asyncio.to_thread(make_api_call),
                    timeout=2.0  # 2 second timeout
                )
                
            except asyncio.TimeoutError:
                logger.error("Google Sheets chat logging timed out after 2 seconds")
                return False
            except Exception as api_error:
                logger.error(f"Google Sheets API error: {api_error}")
                return False
            
            logger.info(f"Chat message logged to Google Sheets: {result.get('updates', {}).get('updatedRows', 0)} rows updated")
            return True
            
        except HttpError as e:
            logger.error(f"Google Sheets API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to log chat message to Google Sheets: {e}")
            return False
    
    async def log_course_progress(self, progress_data: Dict[str, Any]) -> bool:
        """
        Log course progress to Google Sheets CourseProgress tab
        
        Args:
            progress_data: Dictionary containing:
                - user_id: str
                - session_id: str
                - course_id: str
                - course_name: str
                - page_number: int
                - total_pages: int
                - completed: bool
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.service or not self.spreadsheet_id:
                logger.warning("Google Sheets service not available")
                return False
            
            # Prepare data row according to schema
            # Schema: user_id | session_id | course_id | course_name | page_number | total_pages | completed | timestamp
            row_data = [
                progress_data.get('user_id', ''),
                progress_data.get('session_id', ''),
                progress_data.get('course_id', ''),
                progress_data.get('course_name', ''),
                str(progress_data.get('page_number', 0)),
                str(progress_data.get('total_pages', 0)),
                'TRUE' if progress_data.get('completed', False) else 'FALSE',
                datetime.utcnow().isoformat()  # timestamp
            ]
            
            # Append to CourseProgress tab
            body = {
                'values': [row_data]
            }
            
            # Use asyncio timeout for the API call
            try:
                # Create a coroutine that wraps the sync API call
                def make_api_call():
                    return self.service.spreadsheets().values().append(
                        spreadsheetId=self.spreadsheet_id,
                        range='CourseProgress!A:H',
                        valueInputOption='RAW',
                        insertDataOption='INSERT_ROWS',
                        body=body
                    ).execute()
                
                # Run the API call with timeout
                result = await asyncio.wait_for(
                    asyncio.to_thread(make_api_call),
                    timeout=2.0  # 2 second timeout
                )
                
            except asyncio.TimeoutError:
                logger.error("Google Sheets course progress logging timed out after 2 seconds")
                return False
            except Exception as api_error:
                logger.error(f"Google Sheets API error: {api_error}")
                return False
            
            logger.info(f"Course progress logged to Google Sheets: {result.get('updates', {}).get('updatedRows', 0)} rows updated")
            return True
            
        except HttpError as e:
            logger.error(f"Google Sheets API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to log course progress to Google Sheets: {e}")
            return False

    def _format_course_statistics(self, course_stats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format course statistics for Google Sheets export
        
        Args:
            course_stats: List of course statistics objects
        
        Returns:
            Dictionary with formatted course statistics
        """
        if not course_stats:
            return {
                'courses_enrolled': 0,
                'total_score': 0,
                'courses_completed': 0,
                'course_details': ''
            }
        
        courses_enrolled = len(course_stats)
        total_score = sum(stat.get('score', 0) for stat in course_stats)
        courses_completed = sum(1 for stat in course_stats if stat.get('tabs_completed', 0) > 0)
        
        # Format course details as a readable string
        course_details = []
        for stat in course_stats:
            course_name = stat.get('course_name', 'Unknown')
            score = stat.get('score', 0)
            tabs_completed = stat.get('tabs_completed', 0)
            level = stat.get('level', 'easy')
            questions_taken = stat.get('total_questions_taken', 0)
            
            detail = f"{course_name}: {score}% ({tabs_completed} tabs, {questions_taken} questions, {level})"
            course_details.append(detail)
        
        return {
            'courses_enrolled': courses_enrolled,
            'total_score': total_score,
            'courses_completed': courses_completed,
            'course_details': ' | '.join(course_details)
        }

    async def export_user_profiles_to_sheet(self, user_profiles: List[Dict[str, Any]]) -> bool:
        """
        Export user profile data to Google Sheets UserProfiles tab
        
        This method creates a single table with user data including:
        - first_name, last_name, email, total_chats, quizzes_taken, day_streak, days_active
        - courses_enrolled, total_course_score, courses_completed, course_details
        
        Args:
            user_profiles: List of user profile dictionaries containing:
                - user_id: str
                - first_name: str
                - last_name: str
                - email: str
                - total_chats: int
                - quizzes_taken: int
                - day_streak: int
                - days_active: int
                - courses_enrolled: int
                - total_course_score: int
                - courses_completed: int
                - course_details: str
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.service or not self.spreadsheet_id:
                logger.warning("Google Sheets service not available")
                return False
            
            # First, ensure the UserProfiles tab exists with proper headers
            headers = [
                'first_name', 'last_name', 'email', 'total_chats', 'quizzes_taken', 
                'day_streak', 'days_active', 'courses_enrolled', 'total_course_score', 
                'courses_completed', 'course_details'
            ]
            self._setup_sheet_tab('UserProfiles', headers)
            
            # Clear existing data (keep headers)
            try:
                # Get the current data to find the last row
                result = self.service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range='UserProfiles!A:A'
                ).execute()
                
                if result.get('values') and len(result['values']) > 1:
                    # Clear all data except headers (from row 2 onwards)
                    clear_range = f'UserProfiles!A2:K{len(result["values"])}'
                    self.service.spreadsheets().values().clear(
                        spreadsheetId=self.spreadsheet_id,
                        range=clear_range
                    ).execute()
                    logger.info(f"Cleared existing data in UserProfiles tab")
                    
            except Exception as e:
                logger.warning(f"Could not clear existing data: {e}")
            
            # Prepare data rows
            rows_data = []
            for profile in user_profiles:
                row_data = [
                    profile.get('first_name', ''),
                    profile.get('last_name', ''),
                    profile.get('email', ''),
                    str(profile.get('total_chats', 0)),
                    str(profile.get('quizzes_taken', 0)),
                    str(profile.get('day_streak', 0)),
                    str(profile.get('days_active', 0)),
                    str(profile.get('courses_enrolled', 0)),
                    str(profile.get('total_course_score', 0)),
                    str(profile.get('courses_completed', 0)),
                    profile.get('course_details', '')
                ]
                rows_data.append(row_data)
            
            if not rows_data:
                logger.warning("No user profiles to export")
                return True
            
            # Export data to Google Sheets
            try:
                body = {
                    'values': rows_data
                }
                
                # Define the API call function for timeout handling
                def make_api_call():
                    return self.service.spreadsheets().values().append(
                        spreadsheetId=self.spreadsheet_id,
                        range='UserProfiles!A:K',
                        valueInputOption='RAW',
                        insertDataOption='INSERT_ROWS',
                        body=body
                    ).execute()
                
                # Run the API call with timeout
                result = await asyncio.wait_for(
                    asyncio.to_thread(make_api_call),
                    timeout=10.0  # Longer timeout for bulk export
                )
                
                logger.info(f"User profiles exported to Google Sheets: {result.get('updates', {}).get('updatedRows', 0)} rows updated")
                return True
                
            except asyncio.TimeoutError:
                logger.error("Google Sheets user profiles export timed out after 10 seconds")
                return False
            except Exception as api_error:
                logger.error(f"Google Sheets API error: {api_error}")
                return False
            
        except HttpError as e:
            logger.error(f"Google Sheets API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to export user profiles to Google Sheets: {e}")
            return False

    async def get_all_user_profiles_for_export(self) -> List[Dict[str, Any]]:
        """
        Helper method to fetch all user profiles with user information for export
        
        Returns:
            List of user profile dictionaries ready for Google Sheets export
        """
        try:
            from app.core.database import get_supabase
            
            supabase = get_supabase()
            
            # Get all user profiles with user information and course statistics
            result = supabase.table('user_profiles').select(
                'user_id, total_chats, quizzes_taken, day_streak, days_active, course_statistics'
            ).execute()
            
            user_profiles = []
            for profile in result.data:
                user_id = profile['user_id']
                
                try:
                    # Get user information (first_name, last_name, email)
                    user_result = supabase.table('users').select(
                        'first_name, last_name, email'
                    ).eq('id', user_id).single().execute()
                    
                    if user_result.data:
                        user_info = user_result.data
                        # Process course statistics
                        course_stats = profile.get('course_statistics', [])
                        course_summary = self._format_course_statistics(course_stats)
                        
                        user_profiles.append({
                            'user_id': user_id,
                            'first_name': user_info.get('first_name', ''),
                            'last_name': user_info.get('last_name', ''),
                            'email': user_info.get('email', ''),
                            'total_chats': profile.get('total_chats', 0),
                            'quizzes_taken': profile.get('quizzes_taken', 0),
                            'day_streak': profile.get('day_streak', 0),
                            'days_active': profile.get('days_active', 0),
                            'courses_enrolled': course_summary['courses_enrolled'],
                            'total_course_score': course_summary['total_score'],
                            'courses_completed': course_summary['courses_completed'],
                            'course_details': course_summary['course_details']
                        })
                    else:
                        # Add profile without user details if user not found
                        course_stats = profile.get('course_statistics', [])
                        course_summary = self._format_course_statistics(course_stats)
                        
                        user_profiles.append({
                            'user_id': user_id,
                            'first_name': 'Unknown',
                            'last_name': 'User',
                            'email': '',
                            'total_chats': profile.get('total_chats', 0),
                            'quizzes_taken': profile.get('quizzes_taken', 0),
                            'day_streak': profile.get('day_streak', 0),
                            'days_active': profile.get('days_active', 0),
                            'courses_enrolled': course_summary['courses_enrolled'],
                            'total_course_score': course_summary['total_score'],
                            'courses_completed': course_summary['courses_completed'],
                            'course_details': course_summary['course_details']
                        })
                except Exception as user_error:
                    logger.warning(f"Could not get user details for {user_id}: {user_error}")
                    # Add profile without user details
                    course_stats = profile.get('course_statistics', [])
                    course_summary = self._format_course_statistics(course_stats)
                    
                    user_profiles.append({
                        'user_id': user_id,
                        'first_name': 'Unknown',
                        'last_name': 'User',
                        'email': '',
                        'total_chats': profile.get('total_chats', 0),
                        'quizzes_taken': profile.get('quizzes_taken', 0),
                        'day_streak': profile.get('day_streak', 0),
                        'days_active': profile.get('days_active', 0),
                        'courses_enrolled': course_summary['courses_enrolled'],
                        'total_course_score': course_summary['total_score'],
                        'courses_completed': course_summary['courses_completed'],
                        'course_details': course_summary['course_details']
                    })
            
            logger.info(f"Retrieved {len(user_profiles)} user profiles for export")
            return user_profiles
            
        except Exception as e:
            logger.error(f"Failed to get user profiles for export: {e}")
            return [] 