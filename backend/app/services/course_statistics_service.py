from typing import Dict, Any, List, Optional
import logging
import asyncio
from datetime import datetime, timedelta
from app.core.database import get_supabase

logger = logging.getLogger(__name__)

class CourseStatisticsService:
    """
    Service for calculating course statistics from existing data.
    
    IMPORTANT: This service only updates the database. Google Sheets sync is handled
    exclusively by the background sync service to maintain a single source of truth.
    
    Data sources:
    - quiz_responses: For quiz attempts, scores, and timestamps
    - user_course_sessions: For course progress (when available)
    - courses: For proper course naming
    """
    
    def __init__(self):
        self.supabase = get_supabase()
    
    async def calculate_user_course_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Calculate comprehensive course statistics for a user from existing data
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with aggregated course statistics
        """
        try:
            # Get comprehensive quiz responses for the user
            quiz_responses = await asyncio.to_thread(
                lambda: self.supabase.table('quiz_responses').select(
                    'quiz_id, topic, correct, timestamp, score, course_id, quiz_type, created_at, page_index'
                ).eq('user_id', user_id).execute()
            )
            
            # Get user course sessions data for progress tracking
            user_course_sessions = await asyncio.to_thread(
                lambda: self.supabase.table('user_course_sessions').select('*').eq('user_id', user_id).execute()
            )
            
            # Get course information for proper naming
            courses_result = await asyncio.to_thread(
                lambda: self.supabase.table('courses').select('id, title, topic').execute()
            )
            course_mapping = {course['id']: course['title'] for course in courses_result.data} if courses_result.data else {}
            
            # Create separate rows for each course session instead of aggregating
            course_sessions = {}
            
            # Process quiz responses for accurate statistics - group by course + session
            for response in quiz_responses.data:
                topic = response.get('topic', 'Unknown')
                course_id = response.get('course_id')
                session_id = response.get('session_id', 'unknown')
                
                # Determine course name - prioritize course_id mapping, then topic mapping
                if course_id and course_id in course_mapping:
                    course_name = course_mapping[course_id]
                else:
                    # For diagnostic tests, use topic mapping to get human-readable names
                    course_name = self._map_topic_to_course(topic)
                
                # Log the mapping for debugging
                logger.debug(f"Quiz response mapping: topic='{topic}', course_id='{course_id}' -> course_name='{course_name}'")
                
                # Create unique key for course + session combination
                session_key = f"{course_name}_{session_id}"
                
                if session_key not in course_sessions:
                    # Create a new session record
                    course_sessions[session_key] = {
                        'course_name': course_name,
                        'total_questions_taken': 0,
                        'correct_answers': 0,
                        'score': 0,
                        'tabs_completed': 0,  # Will be updated if session data exists
                        'level': 'beginner',  # Will be calculated later
                        'last_activity': response.get('timestamp') or response.get('created_at'),
                        'quiz_types': set(),
                        'course_id': course_id,
                        'session_id': session_id,
                        'attempt_timestamp': response.get('timestamp') or response.get('created_at')
                    }
                
                # Update session statistics
                course_sessions[session_key]['total_questions_taken'] += 1
                if response.get('correct', False):
                    course_sessions[session_key]['correct_answers'] += 1
                
                # Track quiz types
                quiz_type = response.get('quiz_type', 'unknown')
                course_sessions[session_key]['quiz_types'].add(quiz_type)
                
                # Update last activity if this response is more recent
                timestamp = response.get('timestamp') or response.get('created_at')
                if timestamp and (not course_sessions[session_key]['last_activity'] or timestamp > course_sessions[session_key]['last_activity']):
                    course_sessions[session_key]['last_activity'] = timestamp
                    logger.debug(f"Updated last activity for {course_name} session {session_id}: {timestamp}")
            
            # Convert to list for processing
            course_attempts = list(course_sessions.values())
            
            # Process user course sessions for progress tracking
            if user_course_sessions.data:
                for session in user_course_sessions.data:
                    course_id = session.get('course_id')
                    
                    # Get course name from course mapping or fallback
                    if course_id and course_id in course_mapping:
                        course_name = course_mapping[course_id]
                    else:
                        course_name = f'Course {course_id[:8] if course_id else "Unknown"}'
                    
                    # Find matching course attempts to update tabs completed
                    for attempt in course_attempts:
                        if attempt['course_id'] == course_id:
                            # Update tabs completed - use the highest page number from available fields
                            available_page_fields = []
                            for field in ['current_page', 'page_number', 'page_index', 'page']:
                                if session.get(field) is not None:
                                    available_page_fields.append(session.get(field))
                            
                            current_page = max(available_page_fields) if available_page_fields else 0
                            
                            if current_page > attempt['tabs_completed']:
                                attempt['tabs_completed'] = current_page
                                logger.debug(f"Updated tabs completed for {course_name}: {current_page}")
                            
                            # Update last activity from session if it's more recent
                            updated_at = session.get('updated_at')
                            if updated_at and (not attempt['last_activity'] or updated_at > attempt['last_activity']):
                                attempt['last_activity'] = updated_at
                                logger.debug(f"Updated last activity from session for {course_name}: {updated_at}")
            else:
                # No course sessions found - this is normal for users who only took diagnostic tests
                logger.info(f"No course sessions found for user {user_id} - this is normal for diagnostic-only users")
            
            # Calculate final statistics and clean up data for each attempt
            final_stats = []
            for attempt in course_attempts:
                # Calculate accurate score percentage - ensure no division by zero
                if attempt['total_questions_taken'] > 0:
                    raw_score = (attempt['correct_answers'] / attempt['total_questions_taken']) * 100
                    attempt['score'] = round(raw_score)
                    logger.debug(f"Score calculation for {attempt['course_name']}: {attempt['correct_answers']}/{attempt['total_questions_taken']} = {raw_score}% -> {attempt['score']}%")
                else:
                    attempt['score'] = 0
                    logger.debug(f"No questions taken for {attempt['course_name']}, score set to 0")
                
                # Determine level based on score and activity
                attempt['level'] = self._determine_level(attempt['score'], attempt['total_questions_taken'])
                logger.debug(f"Level determination for {attempt['course_name']}: score={attempt['score']}%, questions={attempt['total_questions_taken']} -> level={attempt['level']}")
                
                # Convert quiz_types set to list for JSON serialization
                attempt['quiz_types'] = list(attempt['quiz_types'])
                
                # Format last activity for better readability
                if attempt['last_activity']:
                    try:
                        # Convert to datetime and format
                        if isinstance(attempt['last_activity'], str):
                            from datetime import datetime
                            dt = datetime.fromisoformat(attempt['last_activity'].replace('Z', '+00:00'))
                            attempt['last_activity'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                            logger.debug(f"Formatted last activity for {attempt['course_name']}: {attempt['last_activity']}")
                    except Exception as e:
                        # Keep original if parsing fails
                        logger.warning(f"Failed to format last activity for {attempt['course_name']}: {e}")
                        pass
                
                # Remove internal fields before returning
                fields_to_remove = ['course_id', 'quiz_id', 'session_id', 'attempt_timestamp']
                for field in fields_to_remove:
                    if field in attempt:
                        del attempt[field]
                
                final_stats.append(attempt)
            
            # Log final summary for debugging
            logger.info(f"Calculated course statistics for user {user_id}: {len(final_stats)} course attempts")
            for stat in final_stats:
                logger.info(f"  - {stat['course_name']}: {stat['correct_answers']}/{stat['total_questions_taken']} correct = {stat['score']}%, level={stat['level']}")
            
            return final_stats
            
        except Exception as e:
            logger.error(f"Error calculating course statistics for user {user_id}: {e}")
            return []
    
    async def update_user_profile_statistics(self, user_id: str) -> bool:
        """
        Update user profile with calculated course statistics
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Calculate course statistics
            course_stats = await self.calculate_user_course_statistics(user_id)
            
            # Update user profile
            update_data = {
                'course_statistics': course_stats,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            result = await asyncio.to_thread(
                lambda: self.supabase.table('user_profiles').update(update_data).eq('user_id', user_id).execute()
            )
            
            if result.data:
                logger.info(f"Updated course statistics for user {user_id}: {len(course_stats)} courses")
                return True
            else:
                logger.warning(f"No user profile found for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating user profile statistics for user {user_id}: {e}")
            return False
    
    async def update_all_user_statistics(self) -> Dict[str, Any]:
        """
        Update course statistics for all users
        
        Returns:
            Dictionary with update results
        """
        try:
            # Get all user profiles
            result = await asyncio.to_thread(
                lambda: self.supabase.table('user_profiles').select('user_id').execute()
            )
            
            if not result.data:
                return {'success': False, 'message': 'No users found', 'updated': 0}
            
            updated_count = 0
            failed_count = 0
            
            for user_profile in result.data:
                user_id = user_profile['user_id']
                success = await self.update_user_profile_statistics(user_id)
                
                if success:
                    updated_count += 1
                else:
                    failed_count += 1
            
            return {
                'success': True,
                'message': f'Updated {updated_count} users, failed {failed_count}',
                'updated': updated_count,
                'failed': failed_count,
                'total': len(result.data)
            }
            
        except Exception as e:
            logger.error(f"Error updating all user statistics: {e}")
            return {'success': False, 'message': str(e), 'updated': 0}
    
    def _map_topic_to_course(self, topic: str) -> str:
        """
        Map quiz topic to course name
        
        Args:
            topic: Quiz topic
            
        Returns:
            Course name
        """
        # Direct mapping for known course types
        course_mapping = {
            'money-goals-mindset': 'Money, Goals and Mindset',
            'budgeting-saving': 'Budgeting and Saving',
            'college-planning-saving': 'College Planning and Saving',
            'earning-income-basics': 'Earning and Income Basics'
        }
        
        # Check if it's a known course type first
        if topic in course_mapping:
            return course_mapping[topic]
        
        # Fallback to keyword-based mapping
        topic_lower = topic.lower()
        
        if any(word in topic_lower for word in ['budget', 'save', 'expense', 'income']):
            return 'Budgeting and Saving'
        elif any(word in topic_lower for word in ['goal', 'mindset', 'financial']):
            return 'Money, Goals and Mindset'
        elif any(word in topic_lower for word in ['invest', 'stock', 'bond', 'portfolio']):
            return 'Investing Basics'
        elif any(word in topic_lower for word in ['debt', 'credit', 'loan', 'interest']):
            return 'Debt Management'
        elif any(word in topic_lower for word in ['emergency', 'safety']):
            return 'Emergency Fund'
        else:
            return 'General Financial Education'
    
    def _determine_level(self, score: int, questions_taken: int) -> str:
        """
        Determine course level based on score and activity
        
        Args:
            score: Percentage score
            questions_taken: Number of questions taken
            
        Returns:
            Level: easy, medium, or hard
        """
        # Need sufficient questions to determine level
        if questions_taken < 3:
            return 'beginner'
        elif questions_taken < 8:
            # Limited questions - level based on score
            if score >= 80:
                return 'intermediate'
            elif score >= 60:
                return 'beginner'
            else:
                return 'beginner'
        else:
            # Sufficient questions - more accurate level determination
            if score >= 85:
                return 'advanced'
            elif score >= 70:
                return 'intermediate'
            elif score >= 50:
                return 'beginner'
            else:
                return 'beginner'
