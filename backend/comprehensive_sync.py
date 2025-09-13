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
os.environ['GOOGLE_SHEETS_SPREADSHEET_ID'] = '1vAQcl58-j_EWD02F7Dw3YPGBY9OurKXs5hV8EMxg10I'

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

            self.sheets_service = GoogleSheetsService()
            self.supabase = get_supabase()

            logger.info("✅ Services initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize services: {e}")
            return False

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
            # Get user profiles with incremental logic
            if last_sync:
                result = self.supabase.table('user_profiles').select(
                    'user_id, total_chats, quizzes_taken, day_streak, days_active, course_statistics, updated_at'
                ).gte('updated_at', last_sync.isoformat()).execute()
            else:
                result = self.supabase.table('user_profiles').select(
                    'user_id, total_chats, quizzes_taken, day_streak, days_active, course_statistics'
                ).execute()

            if not result.data:
                return {"synced": 0, "message": "No user profiles to sync"}

            # Process profiles
            profiles_data = []
            for profile in result.data:
                user_id = profile['user_id']

                # Get user details
                user_result = self.supabase.table('users').select(
                    'first_name, last_name, email'
                ).eq('id', user_id).single().execute()

                if user_result.data:
                    user_info = user_result.data

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

            # Sync to Google Sheets
            if profiles_data:
                body = {'values': profiles_data}
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        lambda: self.sheets_service.service.spreadsheets().values().append(
                            spreadsheetId=self.sheets_service.spreadsheet_id,
                            range='UserProfiles!A:K',
                            valueInputOption='RAW',
                            insertDataOption='INSERT_ROWS',
                            body=body
                        ).execute()
                    ),
                    timeout=120.0
                )

                return {"synced": len(profiles_data), "message": f"Added {len(profiles_data)} user profiles"}

            return {"synced": 0, "message": "No profiles to sync"}

        except Exception as e:
            logger.error(f"Error syncing user profiles: {e}")
            return {"error": str(e)}

    async def _sync_quiz_responses(self, last_sync: Optional[datetime]) -> Dict[str, Any]:
        """Sync quiz responses from quiz_responses table"""
        try:
            # Get quiz responses
            if last_sync:
                result = self.supabase.table('quiz_responses').select(
                    'user_id, timestamp, quiz_id, topic, selected, correct, session_id, explanation'
                ).gte('created_at', last_sync.isoformat()).execute()
            else:
                result = self.supabase.table('quiz_responses').select(
                    'user_id, timestamp, quiz_id, topic, selected, correct, session_id, explanation'
                ).execute()

            if not result.data:
                return {"synced": 0, "message": "No quiz responses to sync"}

            # Process responses
            responses_data = []
            for response in result.data:
                responses_data.append([
                    response.get('user_id', ''),
                    response.get('timestamp', ''),
                    response.get('quiz_id', ''),
                    response.get('topic', ''),
                    response.get('selected', ''),
                    'TRUE' if response.get('correct', False) else 'FALSE',
                    response.get('session_id', '')
                ])

            # Sync to Google Sheets
            if responses_data:
                body = {'values': responses_data}
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        lambda: self.sheets_service.service.spreadsheets().values().append(
                            spreadsheetId=self.sheets_service.spreadsheet_id,
                            range='QuizResponses!A:G',
                            valueInputOption='RAW',
                            insertDataOption='INSERT_ROWS',
                            body=body
                        ).execute()
                    ),
                    timeout=120.0
                )

                return {"synced": len(responses_data), "message": f"Added {len(responses_data)} quiz responses"}

            return {"synced": 0, "message": "No responses to sync"}

        except Exception as e:
            logger.error(f"Error syncing quiz responses: {e}")
            return {"error": str(e)}

    async def _sync_engagement_logs(self, last_sync: Optional[datetime]) -> Dict[str, Any]:
        """Sync engagement logs from user_sessions table"""
        try:
            # Get user sessions
            if last_sync:
                result = self.supabase.table('user_sessions').select(
                    'user_id, id, created_at, updated_at, chat_history, quiz_history, progress'
                ).gte('updated_at', last_sync.isoformat()).execute()
            else:
                result = self.supabase.table('user_sessions').select(
                    'user_id, id, created_at, updated_at, chat_history, quiz_history, progress'
                ).execute()

            if not result.data:
                return {"synced": 0, "message": "No engagement data to sync"}

            # Process sessions
            engagement_data = []
            for session in result.data:
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

            # Sync to Google Sheets
            if engagement_data:
                body = {'values': engagement_data}
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        lambda: self.sheets_service.service.spreadsheets().values().append(
                            spreadsheetId=self.sheets_service.spreadsheet_id,
                            range='EngagementLogs!A:H',
                            valueInputOption='RAW',
                            insertDataOption='INSERT_ROWS',
                            body=body
                        ).execute()
                    ),
                    timeout=120.0
                )

                return {"synced": len(engagement_data), "message": f"Added {len(engagement_data)} engagement logs"}

            return {"synced": 0, "message": "No engagement data to sync"}

        except Exception as e:
            logger.error(f"Error syncing engagement logs: {e}")
            return {"error": str(e)}

    async def _sync_chat_logs(self, last_sync: Optional[datetime]) -> Dict[str, Any]:
        """Sync chat logs from chat_history table"""
        try:
            # Get chat history
            if last_sync:
                result = self.supabase.table('chat_history').select(
                    'user_id, message, role, created_at, session_id'
                ).gte('created_at', last_sync.isoformat()).execute()
            else:
                result = self.supabase.table('chat_history').select(
                    'user_id, message, role, created_at, session_id'
                ).execute()

            if not result.data:
                return {"synced": 0, "message": "No chat logs to sync"}

            # Process chat messages
            chat_data = []
            for chat in result.data:
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

            # Sync to Google Sheets
            if chat_data:
                body = {'values': chat_data}
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
                    timeout=120.0
                )

                return {"synced": len(chat_data), "message": f"Added {len(chat_data)} chat logs"}

            return {"synced": 0, "message": "No chat logs to sync"}

        except Exception as e:
            logger.error(f"Error syncing chat logs: {e}")
            return {"error": str(e)}

    async def _sync_course_progress(self, last_sync: Optional[datetime]) -> Dict[str, Any]:
        """Sync course progress from user_course_sessions table"""
        try:
            # Get course sessions
            if last_sync:
                result = self.supabase.table('user_course_sessions').select(
                    'user_id, course_id, current_page_index, completed, started_at, completed_at, updated_at'
                ).gte('updated_at', last_sync.isoformat()).execute()
            else:
                result = self.supabase.table('user_course_sessions').select(
                    'user_id, course_id, current_page_index, completed, started_at, completed_at, updated_at'
                ).execute()

            if not result.data:
                return {"synced": 0, "message": "No course progress to sync"}

            # Get course names
            courses_result = self.supabase.table('courses').select('id, title').execute()
            course_names = {course['id']: course['title'] for course in courses_result.data}

            # Process course progress
            progress_data = []
            for session in result.data:
                course_id = session.get('course_id')
                course_name = course_names.get(course_id, f'Course {course_id}')

                # Get total pages for this course
                pages_result = self.supabase.table('course_pages').select('id').eq('course_id', course_id).execute()
                total_pages = len(pages_result.data)

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

            # Sync to Google Sheets
            if progress_data:
                body = {'values': progress_data}
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        lambda: self.sheets_service.service.spreadsheets().values().append(
                            spreadsheetId=self.sheets_service.spreadsheet_id,
                            range='CourseProgress!A:H',
                            valueInputOption='RAW',
                            insertDataOption='INSERT_ROWS',
                            body=body
                        ).execute()
                    ),
                    timeout=120.0
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