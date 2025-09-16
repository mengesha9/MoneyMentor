#!/usr/bin/env python3
"""
Comprehensive Google Sheets Sync Script
Syncs all data from Supabase to Google Sheets tabs
"""
import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Set up environment
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './google-credentials.json'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveSyncService:
    """Service to sync all data from Supabase to Google Sheets"""

    def __init__(self):
        self.sheets_service = None
        self.supabase = None
        self.last_sync_time = None

    async def initialize(self):
        """Initialize services"""
        try:
            from app.services.google_sheets_service import GoogleSheetsService
            from app.core.database import get_supabase

            # Run initialization in thread pool to avoid blocking
            self.sheets_service = await asyncio.to_thread(GoogleSheetsService)
            self.supabase = get_supabase()

            # Ensure all required tabs exist
            await self._ensure_tabs_exist()

            logger.info("✅ Services initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize services: {e}")
            return False

    async def _clear_sheet_data(self, sheet_range: str) -> bool:
        """Clear existing data in a sheet range before writing new data"""
        try:
            logger.info(f"🗑️ Clearing existing data in {sheet_range}")
            
            # Parse the range to get proper clear range
            # Convert "TabName!A:K" to "TabName!A2:K" to preserve headers
            if '!' in sheet_range:
                tab_name, range_part = sheet_range.split('!', 1)
                if ':' in range_part:
                    start_col, end_col = range_part.split(':')
                    # If start is just a column letter (like A), make it A2
                    if start_col.isalpha():
                        start_col = start_col + '2'
                    clear_range = f"{tab_name}!{start_col}:{end_col}"
                else:
                    # Single cell reference, start from row 2
                    clear_range = f"{tab_name}!{range_part}2:{range_part}"
            else:
                # If no tab specified, assume current sheet
                clear_range = sheet_range
            
            await asyncio.to_thread(
                lambda: self.sheets_service.service.spreadsheets().values().clear(
                    spreadsheetId=self.sheets_service.spreadsheet_id,
                    range=clear_range
                ).execute()
            )
            
            logger.info(f"✅ Successfully cleared {sheet_range}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to clear {sheet_range}: {e}")
            return False

    async def _ensure_tabs_exist(self):
        """Ensure all required tabs exist in the Google Sheet"""
        try:
            logger.info("🔍 Checking if all required tabs exist...")
            
            # Define required tabs with their headers
            required_tabs = {
                'UserProfiles': [
                    'User ID', 'First Name', 'Last Name', 'Email', 'Total Chats', 
                    'Quizzes Taken', 'Day Streak', 'Days Active', 'Course Statistics', 
                    'Created At', 'Updated At'
                ],
                'QuizResponses': [
                    'User ID', 'Timestamp', 'Quiz ID', 'Topic', 'Selected', 
                    'Correct', 'Session ID'
                ],
                'EngagementLogs': [
                    'User ID', 'Event Type', 'Event Data', 'Timestamp', 
                    'Session ID', 'Page', 'Course ID', 'Additional Data'
                ],
                'ChatLogs': [
                    'User ID', 'Message', 'Role', 'Created At', 'Session ID', 'Page'
                ],
                'CourseProgress': [
                    'User ID', 'Course ID', 'Course Title', 'Current Page', 
                    'Total Pages', 'Progress %', 'Completed', 'Started At'
                ],
                'course_statistics': [
                    'User ID', 'User Name', 'Email', 'Course Attempts', 'Course Details'
                ],
                'ConfidencePolls': [
                    'User ID', 'Topic', 'Confidence Level', 'Timestamp', 
                    'Session ID', 'Course ID'
                ],
                'UsageLogs': [
                    'User ID', 'Action', 'Timestamp', 'Session ID', 
                    'Page', 'Duration', 'Additional Data'
                ]
            }
            
            # Get existing sheet info
            sheet_info = await asyncio.to_thread(self.sheets_service.get_sheet_info)
            existing_tabs = sheet_info.get('sheets', []) if sheet_info else []
            
            logger.info(f"📋 Found {len(existing_tabs)} existing tabs: {existing_tabs}")
            
            # Check which tabs need to be created
            tabs_to_create = []
            for tab_name in required_tabs:
                if tab_name not in existing_tabs:
                    tabs_to_create.append(tab_name)
            
            if tabs_to_create:
                logger.info(f"📝 Creating missing tabs: {tabs_to_create}")
                
                # Create missing tabs
                for tab_name in tabs_to_create:
                    try:
                        await self._create_tab_with_headers(tab_name, required_tabs[tab_name])
                        logger.info(f"✅ Created tab: {tab_name}")
                    except Exception as e:
                        logger.error(f"❌ Failed to create tab {tab_name}: {e}")
            else:
                logger.info("✅ All required tabs already exist")
                
        except Exception as e:
            logger.error(f"❌ Error ensuring tabs exist: {e}")
            # Continue anyway, as tabs might exist but we can't check them
    
    async def _create_tab_with_headers(self, tab_name: str, headers: List[str]):
        """Create a new tab with headers"""
        try:
            # Add worksheet
            await asyncio.to_thread(
                lambda: self.sheets_service.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.sheets_service.spreadsheet_id,
                    body={
                        'requests': [{
                            'addSheet': {
                                'properties': {
                                    'title': tab_name
                                }
                            }
                        }]
                    }
                ).execute()
            )
            
            # Add headers to the new tab
            await asyncio.to_thread(
                lambda: self.sheets_service.service.spreadsheets().values().update(
                    spreadsheetId=self.sheets_service.spreadsheet_id,
                    range=f'{tab_name}!A1',
                    valueInputOption='RAW',
                    body={'values': [headers]}
                ).execute()
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to create tab {tab_name}: {e}")
            raise

    async def sync_all_tabs(self, incremental: bool = False) -> Dict[str, Any]:
        """
        Sync all tabs from Supabase to Google Sheets

        Args:
            incremental: If True, only sync data since last sync

        Returns:
            Dict with sync results for each tab
        """
        results = {}

        if not self.sheets_service or not self.supabase:
            logger.error("Services not initialized")
            return {"error": "Services not initialized"}

        # Determine sync time
        sync_time = datetime.utcnow()
        last_sync = self.last_sync_time if incremental else None

        logger.info(f"🔄 Starting {'incremental' if incremental else 'full'} sync...")

        # Sync each tab
        sync_operations = [
            ('UserProfiles', self._sync_user_profiles, last_sync),
            ('QuizResponses', self._sync_quiz_responses, last_sync),
            ('EngagementLogs', self._sync_engagement_logs, last_sync),
            ('ChatLogs', self._sync_chat_logs, last_sync),
            ('CourseProgress', self._sync_course_progress, last_sync),
            ('course_statistics', self._sync_course_statistics, last_sync),
            ('ConfidencePolls', self._sync_confidence_polls, last_sync),
            ('UsageLogs', self._sync_usage_logs, last_sync),
        ]

        for tab_name, sync_func, sync_param in sync_operations:
            try:
                logger.info(f"📊 Syncing {tab_name}...")
                result = await sync_func(sync_param)
                results[tab_name] = result
                logger.info(f"✅ {tab_name}: {result}")
            except Exception as e:
                logger.error(f"❌ {tab_name} sync failed: {e}")
                results[tab_name] = {"error": str(e)}

        # Update last sync time
        self.last_sync_time = sync_time

        logger.info("🎉 Sync completed!")
        return results

    async def _sync_user_profiles(self, last_sync: Optional[datetime]) -> Dict[str, Any]:
        """Sync user profiles from user_profiles table"""
        try:
            # Get user profiles with incremental logic - wrap in asyncio.to_thread for non-blocking
            if last_sync:
                result = await asyncio.to_thread(
                    lambda: self.supabase.table('user_profiles').select(
                        'user_id, total_chats, quizzes_taken, day_streak, days_active, course_statistics, updated_at'
                    ).gte('updated_at', last_sync.isoformat()).execute()
                )
            else:
                result = await asyncio.to_thread(
                    lambda: self.supabase.table('user_profiles').select(
                        'user_id, total_chats, quizzes_taken, day_streak, days_active, course_statistics'
                    ).execute()
                )

            if not result.data:
                return {"synced": 0, "message": "No user profiles to sync"}

            # Get all user details in one bulk query - wrap in asyncio.to_thread for non-blocking
            user_ids = [profile['user_id'] for profile in result.data]
            users_result = await asyncio.to_thread(
                lambda: self.supabase.table('users').select(
                    'id, first_name, last_name, email'
                ).in_('id', user_ids).execute()
            )
            
            # Create user lookup dict for faster access
            users_dict = {user['id']: user for user in users_result.data}

            # Process profiles in smaller batches to avoid blocking
            profiles_data = []
            batch_size = 10
            
            for i in range(0, len(result.data), batch_size):
                batch = result.data[i:i + batch_size]
                
                for profile in batch:
                    user_id = profile['user_id']
                    user_info = users_dict.get(user_id, {})

                    if user_info:
                        # Process course statistics
                        course_stats = profile.get('course_statistics', [])
                        courses_enrolled = len(course_stats) if course_stats else 0
                        total_score = sum(stat.get('score', 0) for stat in course_stats) if course_stats else 0
                        courses_completed = sum(1 for stat in course_stats if stat.get('tabs_completed', 0) > 0) if course_stats else 0

                        # Format course details
                        course_details = ""
                        if course_stats:
                            details = []
                            for stat in course_stats:
                                course_name = stat.get('course_name', 'Unknown')
                                score = stat.get('score', 0)
                                details.append(f"{course_name}: {score}%")
                            course_details = " | ".join(details)

                        profiles_data.append([
                            user_info.get('first_name', ''),
                            user_info.get('last_name', ''),
                            user_info.get('email', ''),
                            str(profile.get('total_chats', 0)),
                            str(profile.get('quizzes_taken', 0)),
                            str(profile.get('day_streak', 0)),
                            str(profile.get('days_active', 0)),
                            str(courses_enrolled),
                            str(total_score),
                            str(courses_completed),
                            course_details
                        ])
                
                # Yield control after each batch to prevent blocking
                if i + batch_size < len(result.data):
                    await asyncio.sleep(0.01)  # Small delay to yield control

            # Clear existing data before syncing (but only for full sync, not incremental)
            if not last_sync:
                await self._clear_sheet_data('UserProfiles!A:K')

            # Sync to Google Sheets - wrap execute() in asyncio.to_thread for non-blocking
            if profiles_data:
                body = {'values': profiles_data}
                if last_sync:
                    # For incremental sync, append the data
                    result = await asyncio.to_thread(
                        lambda: self.sheets_service.service.spreadsheets().values().append(
                            spreadsheetId=self.sheets_service.spreadsheet_id,
                            range='UserProfiles!A:K',
                            valueInputOption='RAW',
                            insertDataOption='INSERT_ROWS',
                            body=body
                        ).execute()
                    )
                else:
                    # For full sync, update starting from row 2 (preserve headers)
                    result = await asyncio.to_thread(
                        lambda: self.sheets_service.service.spreadsheets().values().update(
                            spreadsheetId=self.sheets_service.spreadsheet_id,
                            range='UserProfiles!A2:K',
                            valueInputOption='RAW',
                            body=body
                        ).execute()
                    )

                return {"synced": len(profiles_data), "message": f"Added {len(profiles_data)} user profiles"}

            return {"synced": 0, "message": "No profiles to sync"}

        except Exception as e:
            logger.error(f"Error syncing user profiles: {e}")
            return {"error": str(e)}

    async def _sync_quiz_responses(self, last_sync: Optional[datetime]) -> Dict[str, Any]:
        """Sync quiz responses from quiz_responses table"""
        try:
            # Get quiz responses - wrap in asyncio.to_thread for non-blocking
            if last_sync:
                result = await asyncio.to_thread(
                    lambda: self.supabase.table('quiz_responses').select(
                        'user_id, timestamp, quiz_id, topic, selected, correct, session_id, explanation'
                    ).gte('created_at', last_sync.isoformat()).limit(1000).execute()
                )
            else:
                result = await asyncio.to_thread(
                    lambda: self.supabase.table('quiz_responses').select(
                        'user_id, timestamp, quiz_id, topic, selected, correct, session_id, explanation'
                    ).limit(1000).execute()
                )

            if not result.data:
                return {"synced": 0, "message": "No quiz responses to sync"}

            # Process responses in smaller batches
            responses_data = []
            batch_size = 50
            
            for i in range(0, len(result.data), batch_size):
                batch = result.data[i:i + batch_size]
                
                for response in batch:
                    responses_data.append([
                        response.get('user_id', ''),
                        response.get('timestamp', ''),
                        response.get('quiz_id', ''),
                        response.get('topic', ''),
                        response.get('selected', ''),
                        'TRUE' if response.get('correct', False) else 'FALSE',
                        response.get('session_id', '')
                    ])
                
                # Yield control after each batch
                if i + batch_size < len(result.data):
                    await asyncio.sleep(0.01)

            # Clear existing data before syncing (but only for full sync, not incremental)
            if not last_sync:
                await self._clear_sheet_data('QuizResponses!A:G')

            # Sync to Google Sheets - wrap execute() in asyncio.to_thread for non-blocking
            if responses_data:
                body = {'values': responses_data}
                if last_sync:
                    # For incremental sync, append the data
                    result = await asyncio.to_thread(
                        lambda: self.sheets_service.service.spreadsheets().values().append(
                            spreadsheetId=self.sheets_service.spreadsheet_id,
                            range='QuizResponses!A:G',
                            valueInputOption='RAW',
                            insertDataOption='INSERT_ROWS',
                            body=body
                        ).execute()
                    )
                else:
                    # For full sync, update starting from row 2 (preserve headers)
                    result = await asyncio.to_thread(
                        lambda: self.sheets_service.service.spreadsheets().values().update(
                            spreadsheetId=self.sheets_service.spreadsheet_id,
                            range='QuizResponses!A2:G',
                            valueInputOption='RAW',
                            body=body
                        ).execute()
                    )

                return {"synced": len(responses_data), "message": f"Added {len(responses_data)} quiz responses"}

            return {"synced": 0, "message": "No responses to sync"}

        except Exception as e:
            logger.error(f"Error syncing quiz responses: {e}")
            return {"error": str(e)}

    async def _sync_engagement_logs(self, last_sync: Optional[datetime]) -> Dict[str, Any]:
        """Sync engagement logs from user_sessions table"""
        try:
            # Get user sessions - wrap in asyncio.to_thread for non-blocking
            if last_sync:
                result = await asyncio.to_thread(
                    lambda: self.supabase.table('user_sessions').select(
                        'user_id, id, created_at, updated_at, chat_history, quiz_history, progress'
                    ).gte('updated_at', last_sync.isoformat()).limit(500).execute()
                )
            else:
                result = await asyncio.to_thread(
                    lambda: self.supabase.table('user_sessions').select(
                        'user_id, id, created_at, updated_at, chat_history, quiz_history, progress'
                    ).limit(500).execute()
                )

            if not result.data:
                return {"synced": 0, "message": "No engagement data to sync"}

            # Process sessions in smaller batches
            engagement_data = []
            batch_size = 25
            
            for i in range(0, len(result.data), batch_size):
                batch = result.data[i:i + batch_size]
                
                for session in batch:
                    chat_history = session.get('chat_history', [])
                    quiz_history = session.get('quiz_history', [])
                    progress = session.get('progress', {})

                    messages_per_session = len(chat_history) if isinstance(chat_history, list) else 0
                    quizzes_attempted = len(quiz_history) if isinstance(quiz_history, list) else 0
                    pretest_completed = progress.get('pretest_completed', False)
                    confidence_rating = progress.get('confidence_rating', '')

                    engagement_data.append([
                        session.get('user_id', ''),
                        session.get('id', ''),
                        str(messages_per_session),
                        '',  # session_duration - would need to calculate
                        str(quizzes_attempted),
                        'TRUE' if pretest_completed else 'FALSE',
                        session.get('updated_at', session.get('created_at', '')),
                        str(confidence_rating)
                    ])
                
                # Yield control after each batch
                if i + batch_size < len(result.data):
                    await asyncio.sleep(0.01)

            # Clear existing data before syncing (but only for full sync, not incremental)
            if not last_sync:
                await self._clear_sheet_data('EngagementLogs!A:H')

            # Sync to Google Sheets - wrap execute() in asyncio.to_thread for non-blocking
            if engagement_data:
                body = {'values': engagement_data}
                if last_sync:
                    # For incremental sync, append the data
                    result = await asyncio.to_thread(
                        lambda: self.sheets_service.service.spreadsheets().values().append(
                            spreadsheetId=self.sheets_service.spreadsheet_id,
                            range='EngagementLogs!A:H',
                            valueInputOption='RAW',
                            insertDataOption='INSERT_ROWS',
                            body=body
                        ).execute()
                    )
                else:
                    # For full sync, update starting from row 2 (preserve headers)
                    result = await asyncio.to_thread(
                        lambda: self.sheets_service.service.spreadsheets().values().update(
                            spreadsheetId=self.sheets_service.spreadsheet_id,
                            range='EngagementLogs!A2:H',
                            valueInputOption='RAW',
                            body=body
                        ).execute()
                    )

                return {"synced": len(engagement_data), "message": f"Added {len(engagement_data)} engagement logs"}

            return {"synced": 0, "message": "No engagement data to sync"}

        except Exception as e:
            logger.error(f"Error syncing engagement logs: {e}")
            return {"error": str(e)}

    async def _sync_chat_logs(self, last_sync: Optional[datetime]) -> Dict[str, Any]:
        """Sync chat logs from chat_history table"""
        try:
            # Get chat history - wrap in asyncio.to_thread for non-blocking
            if last_sync:
                result = await asyncio.to_thread(
                    lambda: self.supabase.table('chat_history').select(
                        'user_id, message, role, created_at, session_id'
                    ).gte('created_at', last_sync.isoformat()).limit(1000).execute()
                )
            else:
                result = await asyncio.to_thread(
                    lambda: self.supabase.table('chat_history').select(
                        'user_id, message, role, created_at, session_id'
                    ).limit(1000).execute()
                )

            if not result.data:
                return {"synced": 0, "message": "No chat logs to sync"}

            # Process chat messages in smaller batches
            chat_data = []
            batch_size = 50
            
            for i in range(0, len(result.data), batch_size):
                batch = result.data[i:i + batch_size]
                
                for chat in batch:
                    role = chat.get('role', '')
                    message_type = 'assistant' if role == 'assistant' else 'user'

                    chat_data.append([
                        chat.get('user_id', ''),
                        chat.get('session_id', ''),
                        chat.get('created_at', ''),
                        message_type,
                        chat.get('message', ''),
                        ''  # response - would need to pair messages
                    ])
                
                # Yield control after each batch
                if i + batch_size < len(result.data):
                    await asyncio.sleep(0.01)

            # Clear existing data before syncing (but only for full sync, not incremental)
            if not last_sync:
                await self._clear_sheet_data('ChatLogs!A:F')

            # Sync to Google Sheets
            if chat_data:
                body = {'values': chat_data}
                if last_sync:
                    # For incremental sync, append the data
                    result = await asyncio.wait_for(
                        asyncio.to_thread(
                            lambda: self.sheets_service.service.spreadsheets().values().append(
                                spreadsheetId=self.sheets_service.spreadsheet_id,
                                range='ChatLogs!A:F',
                                valueInputOption='RAW',
                                insertDataOption='INSERT_ROWS',
                                body=body
                            ).execute()
                        ),
                        timeout=30.0
                    )
                else:
                    # For full sync, update starting from row 2 (preserve headers)
                    result = await asyncio.wait_for(
                        asyncio.to_thread(
                            lambda: self.sheets_service.service.spreadsheets().values().update(
                                spreadsheetId=self.sheets_service.spreadsheet_id,
                                range='ChatLogs!A2:F',
                                valueInputOption='RAW',
                                body=body
                            ).execute()
                        ),
                        timeout=30.0
                    )

                return {"synced": len(chat_data), "message": f"Added {len(chat_data)} chat logs"}

            return {"synced": 0, "message": "No chat logs to sync"}

        except Exception as e:
            logger.error(f"Error syncing chat logs: {e}")
            return {"error": str(e)}

    async def _sync_course_progress(self, last_sync: Optional[datetime]) -> Dict[str, Any]:
        """Sync course progress from user_course_sessions table"""
        try:
            # Get course sessions - wrap in asyncio.to_thread for non-blocking
            if last_sync:
                result = await asyncio.to_thread(
                    lambda: self.supabase.table('user_course_sessions').select(
                        'user_id, course_id, current_page_index, completed, started_at, completed_at, updated_at'
                    ).gte('updated_at', last_sync.isoformat()).limit(500).execute()
                )
            else:
                result = await asyncio.to_thread(
                    lambda: self.supabase.table('user_course_sessions').select(
                        'user_id, course_id, current_page_index, completed, started_at, completed_at, updated_at'
                    ).limit(500).execute()
                )

            if not result.data:
                return {"synced": 0, "message": "No course progress to sync"}

            # Get course names and pages in bulk - wrap in asyncio.to_thread for non-blocking
            courses_result = await asyncio.to_thread(
                lambda: self.supabase.table('courses').select('id, title').execute()
            )
            course_names = {course['id']: course['title'] for course in courses_result.data}

            # Get course pages in bulk
            course_ids = list(set(session.get('course_id') for session in result.data))
            pages_result = await asyncio.to_thread(
                lambda: self.supabase.table('course_pages').select('course_id, id').in_('course_id', course_ids).execute()
            )
            
            # Count pages per course
            course_page_counts = {}
            for page in pages_result.data:
                course_id = page['course_id']
                course_page_counts[course_id] = course_page_counts.get(course_id, 0) + 1

            # Process course progress in smaller batches
            progress_data = []
            batch_size = 25
            
            for i in range(0, len(result.data), batch_size):
                batch = result.data[i:i + batch_size]
                
                for session in batch:
                    course_id = session.get('course_id')
                    course_name = course_names.get(course_id, f'Course {course_id}')
                    total_pages = course_page_counts.get(course_id, 0)

                    progress_data.append([
                        session.get('user_id', ''),
                        '',  # session_id - not directly available
                        str(course_id),
                        course_name,
                        str(session.get('current_page_index', 0)),
                        str(total_pages),
                        'TRUE' if session.get('completed', False) else 'FALSE',
                        session.get('completed_at', session.get('updated_at', ''))
                    ])
                
                # Yield control after each batch
                if i + batch_size < len(result.data):
                    await asyncio.sleep(0.01)

            # Clear existing data before syncing (but only for full sync, not incremental)
            if not last_sync:
                await self._clear_sheet_data('CourseProgress!A:H')

            # Sync to Google Sheets - wrap execute() in asyncio.to_thread for non-blocking
            if progress_data:
                body = {'values': progress_data}
                if last_sync:
                    # For incremental sync, append the data
                    result = await asyncio.to_thread(
                        lambda: self.sheets_service.service.spreadsheets().values().append(
                            spreadsheetId=self.sheets_service.spreadsheet_id,
                            range='CourseProgress!A:H',
                            valueInputOption='RAW',
                            insertDataOption='INSERT_ROWS',
                            body=body
                        ).execute()
                    )
                else:
                    # For full sync, update starting from row 2 (preserve headers)
                    result = await asyncio.to_thread(
                        lambda: self.sheets_service.service.spreadsheets().values().update(
                            spreadsheetId=self.sheets_service.spreadsheet_id,
                            range='CourseProgress!A2:H',
                            valueInputOption='RAW',
                            body=body
                        ).execute()
                    )

                return {"synced": len(progress_data), "message": f"Added {len(progress_data)} course progress records"}

            return {"synced": 0, "message": "No course progress to sync"}

        except Exception as e:
            logger.error(f"Error syncing course progress: {e}")
            return {"error": str(e)}

    async def _sync_course_statistics(self, last_sync: Optional[datetime]) -> Dict[str, Any]:
        """Sync course statistics - this is already handled by CourseStatisticsService"""
        try:
            from app.services.course_statistics_sync_service import course_statistics_sync_service

            success = await course_statistics_sync_service.sync_course_statistics_to_sheets()
            if success:
                return {"synced": "unknown", "message": "Course statistics synced via CourseStatisticsService"}
            else:
                return {"error": "Course statistics sync failed"}

        except Exception as e:
            logger.error(f"Error syncing course statistics: {e}")
            return {"error": str(e)}

    async def _sync_confidence_polls(self, last_sync: Optional[datetime]) -> Dict[str, Any]:
        """Sync confidence polls - extract from engagement logs or create placeholder"""
        # For now, this is a placeholder - confidence data is in EngagementLogs
        return {"synced": 0, "message": "Confidence polls data is included in EngagementLogs"}

    async def _sync_usage_logs(self, last_sync: Optional[datetime]) -> Dict[str, Any]:
        """Sync usage logs - this would require additional logging infrastructure"""
        # For now, this is a placeholder - would need to implement usage tracking
        return {"synced": 0, "message": "Usage logs require additional tracking infrastructure"}

async def main():
    """Main function to run comprehensive sync"""
    print("🚀 Starting Comprehensive Google Sheets Sync")
    print("=" * 50)

    # Initialize service
    sync_service = ComprehensiveSyncService()
    if not await sync_service.initialize():
        print("❌ Failed to initialize services")
        return

    # Run full sync
    print("\n🔄 Running full sync of all tabs...")
    results = await sync_service.sync_all_tabs(incremental=False)

    # Print results
    print("\n📊 SYNC RESULTS:")
    print("=" * 30)
    for tab, result in results.items():
        if isinstance(result, dict):
            if "error" in result:
                print(f"❌ {tab}: {result['error']}")
            elif "synced" in result:
                print(f"✅ {tab}: {result['message']}")
            else:
                print(f"⚠️  {tab}: {result}")
        else:
            print(f"⚠️  {tab}: {result}")

    print("\n🎉 Sync completed!")

if __name__ == "__main__":
    asyncio.run(main())