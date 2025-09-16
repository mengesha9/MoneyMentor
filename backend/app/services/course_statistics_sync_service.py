#!/usr/bin/env python3
"""
Course Statistics Sync Service
Automatically syncs course statistics to Google Sheets when users complete quizzes
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from app.services.course_statistics_service import CourseStatisticsService
from app.services.google_sheets_service import GoogleSheetsService
from app.core.database import get_supabase

logger = logging.getLogger(__name__)

class CourseStatisticsSyncService:
    """
    Service to sync course statistics to Google Sheets.
    
    IMPORTANT: This is the ONLY service that should update the course_statistics tab
    in Google Sheets. All other services should only update the database.
    
    This service is called exclusively by the background sync service to maintain
    data consistency and avoid conflicts.
    """
    
    def __init__(self):
        self.course_stats_service = CourseStatisticsService()
        self.sheets_service = GoogleSheetsService()
        self.supabase = get_supabase()
    
    async def sync_course_statistics_to_sheets(self, user_id: str = None) -> bool:
        """
        Sync course statistics to Google Sheets
        
        Args:
            user_id: If provided, sync only this user's data. If None, sync all users.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Starting course statistics sync to Google Sheets")
            
            # Get all users or specific user
            if user_id:
                users_result = await asyncio.to_thread(
                    lambda: self.supabase.table('users').select('id, first_name, last_name, email').eq('id', user_id).execute()
                )
            else:
                users_result = await asyncio.to_thread(
                    lambda: self.supabase.table('users').select('id, first_name, last_name, email').execute()
                )
            
            if not users_result.data:
                logger.warning("No users found for course statistics sync")
                return False
            
            logger.info(f"Processing {len(users_result.data)} users for course statistics sync")
            
            # Prepare headers
            headers = [
                'First Name', 
                'Last Name',
                'Email',
                'Course Name',
                'Total Questions Taken',
                'Score (%)',
                'Current Level',
                'Last Activity'
            ]
            
            # Prepare data rows
            all_course_data = []
            all_course_data.append(headers)  # Add headers as first row
            
            # Process users in batches to prevent blocking
            batch_size = 5  # Process 5 users at a time
            total_users = len(users_result.data)
            
            for i in range(0, total_users, batch_size):
                batch = users_result.data[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(total_users + batch_size - 1)//batch_size}: users {i+1}-{min(i+batch_size, total_users)}")
                
                for user in batch:
                    user_id = user['id']
                    first_name = user.get('first_name', 'Unknown')
                    last_name = user.get('last_name', 'User')
                    email = user.get('email', '')
                    
                    logger.info(f"Processing course statistics for user: {first_name} {last_name} ({email})")
                    
                    # Get course statistics for this user
                    course_stats = await self.course_stats_service.calculate_user_course_statistics(user_id)
                    
                    if course_stats:
                        for course_stat in course_stats:
                            row = [
                                first_name,
                                last_name,
                                email,
                                course_stat.get('course_name', 'Unknown'),
                                course_stat.get('total_questions_taken', 0),
                                course_stat.get('score', 0),
                                course_stat.get('level', 'easy'),
                                course_stat.get('last_activity', 'N/A')
                            ]
                            all_course_data.append(row)
                    else:
                        # Add a row showing no course data for this user
                        row = [
                            first_name,
                            last_name,
                            email,
                            'No courses taken',
                            0,
                            0,
                            'N/A',
                            'N/A'
                        ]
                        all_course_data.append(row)
                
                # Yield control after each batch to prevent blocking the event loop
                if i + batch_size < total_users:
                    await asyncio.sleep(0.1)  # Small delay to yield control
                    logger.info(f"Processed batch {i//batch_size + 1}, yielding control...")
            
            # Debug: Check the structure of our data
            logger.info(f"Generated {len(all_course_data)} rows of course statistics data")
            if all_course_data:
                logger.info(f"Headers: {all_course_data[0]}")
                logger.info(f"Number of headers: {len(all_course_data[0])}")
                if len(all_course_data) > 1:
                    logger.info(f"Sample data row: {all_course_data[1]}")
                    logger.info(f"Number of data columns: {len(all_course_data[1])}")
            
            # Update the course_statistics tab in Google Sheets
            success = await self._update_course_statistics_sheet(all_course_data)
            
            if success:
                logger.info(f"Course statistics sync completed successfully for {len(users_result.data)} users")
            else:
                logger.error("Course statistics sync failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Error in course statistics sync: {e}")
            return False
    
    async def _update_course_statistics_sheet(self, data: List[List[Any]]) -> bool:
        """
        Update the course_statistics tab in Google Sheets
        
        Args:
            data: List of rows to write to the sheet
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Clear existing data in the course_statistics tab
            logger.info("Clearing existing data in course_statistics tab")
            
            # Get current data to find the last row
            result = await asyncio.to_thread(
                lambda: self.sheets_service.service.spreadsheets().values().get(
                    spreadsheetId=self.sheets_service.spreadsheet_id,
                    range='course_statistics!A:A'
                ).execute()
            )
            
            if result.get('values') and len(result['values']) > 1:
                # Clear all data except headers (from row 2 onwards)
                clear_range = f'course_statistics!A2:H{len(result["values"])}'
                await asyncio.to_thread(
                    lambda: self.sheets_service.service.spreadsheets().values().clear(
                        spreadsheetId=self.sheets_service.spreadsheet_id,
                        range=clear_range
                    ).execute()
                )
                logger.info("Cleared existing data")
            
            # Write the new course statistics data
            logger.info("Writing course statistics data to Google Sheets")
            
            body = {
                'values': data
            }
            
            result = await asyncio.to_thread(
                lambda: self.sheets_service.service.spreadsheets().values().update(
                    spreadsheetId=self.sheets_service.spreadsheet_id,
                    range='course_statistics!A1:H' + str(len(data)),
                    valueInputOption='RAW',
                    body=body
                ).execute()
            )
            
            logger.info(f"Course statistics data written successfully: {result.get('updatedCells', 0)} cells updated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update course statistics sheet: {e}")
            return False
    
    async def sync_single_user_course_statistics(self, user_id: str) -> bool:
        """
        Sync course statistics for a single user (triggered by quiz completion)
        
        Args:
            user_id: The user ID to sync
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Syncing course statistics for single user: {user_id}")
            
            # First, update the user's course statistics in the database
            await self.course_stats_service.update_user_profile_statistics(user_id)
            
            # Then sync to Google Sheets
            success = await self.sync_course_statistics_to_sheets(user_id)
            
            if success:
                logger.info(f"Single user course statistics sync completed for user: {user_id}")
            else:
                logger.error(f"Single user course statistics sync failed for user: {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error in single user course statistics sync: {e}")
            return False
    
    async def background_sync_all_users(self):
        """
        Background task to sync all users' course statistics periodically
        This can be called by the background sync service
        """
        try:
            logger.info("Starting background sync of all users' course statistics")
            success = await self.sync_course_statistics_to_sheets()
            
            if success:
                logger.info("Background course statistics sync completed successfully")
            else:
                logger.error("Background course statistics sync failed")
                
        except Exception as e:
            logger.error(f"Error in background course statistics sync: {e}")

# Global instance
course_statistics_sync_service = CourseStatisticsSyncService()
