from typing import List, Dict, Any, Optional
import uuid
import json
import logging
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
import asyncio

from app.core.config import settings
from app.core.database import get_supabase
from app.models.schemas import Course, CoursePage, CourseSession
from app.services.content_service import ContentService
from app.services.google_sheets_service import GoogleSheetsService

logger = logging.getLogger(__name__)

class CourseService:
    """Service for managing courses and course flow"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL_GPT4_MINI,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.7
        )
        self.supabase = get_supabase()
        self.content_service = ContentService()
        self.sheets_service = GoogleSheetsService()
    
    async def register_course(self, course_data: Dict[str, Any]) -> str:
        """Register a new course in the database and save all pages"""
        try:
            # Generate a unique course ID
            course_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()

            # Prepare course record for DB (serialize JSONB fields)
            course_record = {
                'id': course_id,
                'title': course_data.get('title', 'Untitled Course'),
                'module': course_data.get('module', 'General'),
                'track': course_data.get('track', 'High School'),
                'estimated_length': course_data.get('estimated_length', '2,000-2,500 words'),
                'lesson_overview': course_data.get('lesson_overview', 'Course overview'),
                'learning_objectives': json.dumps(course_data.get('learning_objectives', [])),
                'core_concepts': json.dumps(course_data.get('core_concepts', [])),
                'key_terms': json.dumps(course_data.get('key_terms', [])),
                'real_life_scenarios': json.dumps(course_data.get('real_life_scenarios', [])),
                'mistakes_to_avoid': json.dumps(course_data.get('mistakes_to_avoid', [])),
                'action_steps': json.dumps(course_data.get('action_steps', [])),
                'summary': course_data.get('summary', 'Course summary'),
                'reflection_prompt': course_data.get('reflection_prompt', 'Reflection question'),
                'course_level': course_data.get('course_level', 'beginner'),
                'why_recommended': course_data.get('why_recommended', 'Recommended based on diagnostic results'),
                'has_quiz': course_data.get('has_quiz', True),
                'topic': course_data.get('topic', ''),
                'created_at': now,
                'updated_at': now
            }

            # Insert course into DB
            try:
                insert_result = self.supabase.table('courses').insert(course_record).execute()
                logger.info(f"Course inserted into database: {course_id}")
                logger.debug(f"Insert result: {insert_result}")
            except Exception as db_error:
                logger.error(f"Database insertion failed for course {course_id}: {db_error}")
                logger.error(f"Course record data: {course_record}")
                raise

            # Generate and insert course pages (including quiz pages)
            try:
                pages_count = await self._generate_course_pages(course_id, course_data)
                logger.info(f"Successfully generated {pages_count} pages for course {course_id}")
                
                # Verify all pages were created
                if pages_count < 10:
                    logger.warning(f"Course {course_id} only has {pages_count} pages instead of expected 10")
                else:
                    logger.info(f"Course {course_id} has the full {pages_count} pages as expected")
                    
            except Exception as page_error:
                logger.error(f"Failed to generate course pages: {page_error}")
                # Continue - at least the course is registered

            logger.info(f"Course registered successfully: {course_id}")
            return course_id
        except Exception as e:
            logger.error(f"Failed to register course: {e}")
            raise
    
    async def _generate_course_pages(self, course_id: str, course_data: Dict[str, Any]):
        """Generate course pages from course data and save to DB (serialize quiz_data)"""
        try:
            pages = []
            page_index = 0
            now = datetime.utcnow().isoformat()
            
            # Check if this is an AI-generated course
            if course_data.get('ai_generated_pages') and len(course_data['ai_generated_pages']) == 10:
                logger.info(f"Using AI-generated pages for course {course_id}")
                
                # Use AI-generated pages
                for page_data in course_data['ai_generated_pages']:
                    pages.append({
                        'id': str(uuid.uuid4()),
                        'course_id': course_id,
                        'page_index': page_index,
                        'title': page_data.get('title', f"Page {page_index + 1}"),
                        'content': page_data.get('content', 'Content not available'),
                        'page_type': 'content',
                        'created_at': now,
                        'updated_at': now
                    })
                    page_index += 1
                
                logger.info(f"Generated {len(pages)} AI-based pages for course {course_id}")
                return len(pages)
            
            # Fallback to manual page generation for backward compatibility
            logger.info(f"Using manual page generation for course {course_id}")
            
            # Page 1: Introduction and Overview
            pages.append({
                'id': str(uuid.uuid4()),
                'course_id': course_id,
                'page_index': page_index,
                'title': f"Welcome to {course_data['title']}",
                'content': f"# {course_data['title']}\n\n{course_data['lesson_overview']}\n\n## 🎯 What You'll Learn\n" + 
                          "\n".join([f"- {obj}" for obj in course_data['learning_objectives']]),
                'page_type': 'content',
                'created_at': now,
                'updated_at': now
            })
            page_index += 1
            
            # Page 2: Core Concept 1 - In-depth learning
            if course_data['core_concepts']:
                concept = course_data['core_concepts'][0]
                pages.append({
                    'id': str(uuid.uuid4()),
                    'course_id': course_id,
                    'page_index': page_index,
                    'title': f"Understanding {concept['title']}",
                    'content': f"# {concept['title']}\n\n{concept['explanation']}\n\n" +
                              f"## 💡 Key Insights\n" +
                              f"**{concept['metaphor']}**\n\n" +
                              f"## 📚 Deep Dive\n" +
                              f"Let's explore this concept further. Understanding {course_data['topic'].lower()} requires grasping fundamental principles that will serve as the foundation for all your future financial decisions.\n\n" +
                              f"### Why This Matters\n" +
                              f"Your {course_data['course_level']} level means you're building essential knowledge that will help you make informed choices about {course_data['topic'].lower()} throughout your life.",
                    'page_type': 'content',
                    'created_at': now,
                    'updated_at': now
                })
                page_index += 1
            
            # Page 3: Core Concept 2 - Advanced understanding
            pages.append({
                'id': str(uuid.uuid4()),
                'course_id': course_id,
                'page_index': page_index,
                'title': f"Advanced {course_data['topic']} Principles",
                'content': f"# Advanced {course_data['topic']} Principles\n\n" +
                          f"## 🧠 Building on Your Foundation\n" +
                          f"Now that you understand the basics, let's explore more sophisticated concepts in {course_data['topic'].lower()}.\n\n" +
                          f"### Principle 1: Systematic Approach\n" +
                          f"Successful {course_data['topic'].lower()} management requires a systematic, step-by-step approach rather than random actions.\n\n" +
                          f"### Principle 2: Long-term Perspective\n" +
                          f"Every decision you make today about {course_data['topic'].lower()} impacts your future. Think 5-10 years ahead.\n\n" +
                          f"### Principle 3: Continuous Learning\n" +
                          f"The world of {course_data['topic'].lower()} is constantly evolving. Stay informed and adaptable.",
                'page_type': 'content',
                'created_at': now,
                'updated_at': now
            })
            page_index += 1
            
            # Page 4: Key Terms and Definitions - Comprehensive learning
            if course_data['key_terms']:
                key_terms_content = f"# Essential {course_data['topic']} Terminology\n\n"
                key_terms_content += f"## 🔑 Master These Key Terms\n\n"
                for term in course_data['key_terms']:
                    key_terms_content += f"### {term['term']}\n"
                    key_terms_content += f"{term['definition']}\n\n"
                    key_terms_content += f"**Example:** {term['example']}\n\n"
                    key_terms_content += f"**Why It Matters:** Understanding this term helps you communicate effectively about {course_data['topic'].lower()} and make better decisions.\n\n"
                
                pages.append({
                    'id': str(uuid.uuid4()),
                    'course_id': course_id,
                    'page_index': page_index,
                    'title': f"Essential {course_data['topic']} Terms",
                    'content': key_terms_content,
                    'page_type': 'content',
                    'created_at': now,
                    'updated_at': now
                })
                page_index += 1
            
            # Page 5: Real-Life Applications - Practical learning
            if course_data['real_life_scenarios']:
                scenario = course_data['real_life_scenarios'][0]
                pages.append({
                    'id': str(uuid.uuid4()),
                    'course_id': course_id,
                    'page_index': page_index,
                    'title': f"Real-World {course_data['topic']} Applications",
                    'content': f"# {scenario['title']}\n\n{scenario['narrative']}\n\n" +
                              f"## 💭 Learning from Real Examples\n" +
                              f"### What Happened\n" +
                              f"This scenario demonstrates several key principles of {course_data['topic'].lower()} that we've discussed.\n\n" +
                              f"### Key Lessons\n" +
                              f"1. **Planning Matters:** Every successful {course_data['topic'].lower()} strategy starts with careful planning\n" +
                              f"2. **Consistency is Key:** Small, regular actions lead to significant results over time\n" +
                              f"3. **Adaptability:** Being flexible and adjusting your approach when needed\n\n" +
                              f"### How This Applies to You\n" +
                              f"Think about how you can apply these lessons to your own {course_data['topic'].lower()} journey.",
                    'page_type': 'content',
                    'created_at': now,
                    'updated_at': now
                })
                page_index += 1
            
            # Page 6: Strategic Planning - Actionable knowledge
            if course_data['action_steps']:
                action_steps_content = f"# Strategic {course_data['topic']} Planning\n\n"
                action_steps_content += f"## 🚀 Your Action Plan\n\n"
                for i, step in enumerate(course_data['action_steps'], 1):
                    action_steps_content += f"### Step {i}: {step}\n"
                    action_steps_content += f"This step is crucial because it builds the foundation for your {course_data['topic'].lower()} success.\n\n"
                
                action_steps_content += f"## ⚠️ Common Pitfalls to Avoid\n\n"
                for mistake in course_data.get('mistakes_to_avoid', []):
                    action_steps_content += f"### ❌ {mistake}\n"
                    action_steps_content += f"**Why This Happens:** Usually due to lack of planning or rushing into decisions.\n\n"
                    action_steps_content += f"**How to Prevent:** Take time to research and plan before acting.\n\n"
                
                pages.append({
                    'id': str(uuid.uuid4()),
                    'course_id': course_id,
                    'page_index': page_index,
                    'title': f"Strategic {course_data['topic']} Planning",
                    'content': action_steps_content,
                    'page_type': 'content',
                    'created_at': now,
                    'updated_at': now
                })
                page_index += 1
            
            # Page 7: Advanced Strategies - Expert-level knowledge
            pages.append({
                'id': str(uuid.uuid4()),
                'course_id': course_id,
                'page_index': page_index,
                'title': f"Advanced {course_data['topic']} Strategies",
                'content': f"# Advanced {course_data['topic']} Strategies\n\n" +
                          f"## 🎯 Taking Your Knowledge to the Next Level\n\n" +
                          f"### Strategy 1: Systematic Analysis\n" +
                          f"Learn to analyze {course_data['topic'].lower()} situations systematically by breaking them down into components.\n\n" +
                          f"### Strategy 2: Risk Management\n" +
                          f"Understanding how to identify and manage risks in {course_data['topic'].lower()} decisions.\n\n" +
                          f"### Strategy 3: Optimization Techniques\n" +
                          f"Methods for optimizing your {course_data['topic'].lower()} approach for maximum effectiveness.\n\n" +
                          f"## 🧠 Critical Thinking Skills\n" +
                          f"Develop the ability to evaluate {course_data['topic'].lower()} information critically and make informed decisions.",
                'page_type': 'content',
                'created_at': now,
                'updated_at': now
            })
            page_index += 1
            
            # Page 8: Industry Insights - Professional knowledge
            pages.append({
                'id': str(uuid.uuid4()),
                'course_id': course_id,
                'page_index': page_index,
                'title': f"Industry Insights: {course_data['topic']}",
                'content': f"# Industry Insights: {course_data['topic']}\n\n" +
                          f"## 🌟 What the Experts Know\n\n" +
                          f"### Current Trends\n" +
                          f"Stay informed about the latest developments in {course_data['topic'].lower()} that could affect your decisions.\n\n" +
                          f"### Best Practices\n" +
                          f"Learn from successful professionals who have mastered {course_data['topic'].lower()} management.\n\n" +
                          f"### Future Outlook\n" +
                          f"Understanding where {course_data['topic'].lower()} is heading helps you prepare for tomorrow's challenges.\n\n" +
                          f"## 📊 Data-Driven Decisions\n" +
                          f"Learn how to use data and research to make better {course_data['topic'].lower()} choices.",
                'page_type': 'content',
                'created_at': now,
                'updated_at': now
            })
            page_index += 1
            
            # Page 9: Practical Implementation - Hands-on knowledge
            pages.append({
                'id': str(uuid.uuid4()),
                'course_id': course_id,
                'page_index': page_index,
                'title': f"Implementing Your {course_data['topic']} Knowledge",
                'content': f"# Implementing Your {course_data['topic']} Knowledge\n\n" +
                          f"## 🛠️ From Theory to Practice\n\n" +
                          f"### Creating Your Action Plan\n" +
                          f"1. **Assess Your Current Situation**\n" +
                          f"   - Evaluate where you are now with {course_data['topic'].lower()}\n" +
                          f"   - Identify areas for improvement\n\n" +
                          f"2. **Set Specific Goals**\n" +
                          f"   - Make goals measurable and time-bound\n" +
                          f"   - Break large goals into smaller, manageable steps\n\n" +
                          f"3. **Track Your Progress**\n" +
                          f"   - Monitor your {course_data['topic'].lower()} journey\n" +
                          f"   - Celebrate small wins along the way\n\n" +
                          f"### Building Sustainable Habits\n" +
                          f"Learn how to create lasting {course_data['topic'].lower()} habits that stick.",
                'page_type': 'content',
                'created_at': now,
                'updated_at': now
            })
            page_index += 1
            
            # Page 10: Mastery and Next Steps - Comprehensive knowledge
            pages.append({
                'id': str(uuid.uuid4()),
                'course_id': course_id,
                'page_index': page_index,
                'title': f"Mastering {course_data['topic']} - Next Steps",
                'content': f"# Mastering {course_data['topic']} - Next Steps\n\n" +
                          f"## 🎓 You've Built a Strong Foundation\n\n" +
                          f"### What You've Accomplished\n" +
                          f"✅ **Fundamental Understanding:** You now grasp the core principles of {course_data['topic'].lower()}\n\n" +
                          f"✅ **Strategic Thinking:** You can approach {course_data['topic'].lower()} decisions systematically\n\n" +
                          f"✅ **Practical Knowledge:** You have actionable strategies to implement\n\n" +
                          f"✅ **Industry Awareness:** You understand current trends and best practices\n\n" +
                          f"## 🚀 Continuing Your Journey\n\n" +
                          f"### Next Level Learning\n" +
                          f"Consider exploring advanced topics in {course_data['topic'].lower()} or related financial areas.\n\n" +
                          f"### Applying Your Knowledge\n" +
                          f"Start implementing what you've learned today. Remember, knowledge without action is like having a map but never leaving home.\n\n" +
                          f"### Staying Updated\n" +
                          f"Continue learning and staying informed about {course_data['topic'].lower()} developments.\n\n" +
                          f"## 🎯 Your Path Forward\n" +
                          f"You now have the knowledge and tools to make informed {course_data['topic'].lower()} decisions. Use them wisely and continue growing!",
                'page_type': 'content',
                'created_at': now,
                'updated_at': now
            })
            page_index += 1
            
            # Insert all pages
            logger.info(f"Generated {len(pages)} course pages for course {course_id}")
            
            # Insert pages in batches to avoid overwhelming the database
            batch_size = 5
            for i in range(0, len(pages), batch_size):
                batch = pages[i:i + batch_size]
                try:
                    insert_result = self.supabase.table('course_pages').insert(batch).execute()
                    logger.info(f"Inserted batch {i//batch_size + 1} of {(len(pages) + batch_size - 1)//batch_size}")
                except Exception as batch_error:
                    logger.error(f"Failed to insert batch {i//batch_size + 1}: {batch_error}")
                    raise
            
            logger.info(f"Successfully generated and inserted {len(pages)} course pages")
            return len(pages)
            
        except Exception as e:
            logger.error(f"Failed to generate course pages: {e}")
            raise
    
    async def _generate_quiz_question(self, topic: str) -> Optional[Dict[str, Any]]:
        """Generate a single quiz question for a topic"""
        try:
            prompt = (
                f"Generate a multiple-choice question about {topic}. "
                f"Return a JSON object with: 'question' (text), 'choices' (object with keys 'a', 'b', 'c', 'd' and string values), "
                f"'correct_answer' (one of 'a', 'b', 'c', 'd'), and 'explanation' (short explanation for the correct answer). "
                f"Make the question educational and relevant to personal finance. "
                f"IMPORTANT: Target teenage students (13-19 years old). Use age-appropriate examples and language. "
                f"Focus on teen-relevant financial situations like saving for college, first car, phone, etc. "
                f"AVOID complex adult topics like retirement planning, tax deductions, or 529 plans."
            )
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            try:
                question_data = json.loads(response.content)
                if 'question' in question_data and 'choices' in question_data and 'correct_answer' in question_data:
                    return {
                        'question': question_data['question'],
                        'choices': question_data['choices'],
                        'correct_answer': question_data['correct_answer'],
                        'explanation': question_data.get('explanation', '')
                    }
            except Exception as e:
                logger.error(f"Failed to parse quiz question JSON: {e}")
                return None
            return None
        except Exception as e:
            logger.error(f"Failed to generate quiz question: {e}")
            return None
    
    async def start_course(self, user_id: str, course_id: str) -> Dict[str, Any]:
        """Start a course - only if it exists in database"""
        try:
            # First check if course exists in database
            course_result = self.supabase.table('courses').select('*').eq('id', course_id).execute()
            if not course_result.data:
                logger.error(f"Course not found in database: {course_id}")
                return {
                    "success": False,
                    "message": f"Course not found: {course_id}. Please ensure the course is properly registered."
                }
            
            # Wait for course pages to be generated (with retry mechanism)
            max_retries = 5
            retry_delay = 1  # seconds
            
            for attempt in range(max_retries):
                try:
                    # Get the first page from database
                    first_page = await self._get_course_page_from_db(course_id, 0)
                    if first_page:
                        logger.info(f"First page found for course {course_id} on attempt {attempt + 1}")
                        break
                    
                    if attempt < max_retries - 1:
                        logger.info(f"First page not ready for course {course_id}, attempt {attempt + 1}/{max_retries}, waiting {retry_delay}s...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        logger.error(f"First page not found for course {course_id} after {max_retries} attempts")
                        return {
                            "success": False,
                            "message": f"Course pages not ready. Please wait a moment and try again."
                        }
                        
                except Exception as retry_error:
                    if attempt < max_retries - 1:
                        logger.warning(f"Error getting first page on attempt {attempt + 1}: {retry_error}, retrying...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        logger.error(f"Failed to get first page after {max_retries} attempts: {retry_error}")
                        raise
            
            # Verify we have the first page
            if not first_page:
                logger.error(f"First page still not available for course: {course_id}")
                return {
                    "success": False,
                    "message": f"Course pages not ready. Please wait a moment and try again."
                }
            
            # Get total pages count
            total_pages = await self._get_total_pages(course_id)
            logger.info(f"Course {course_id} started successfully with {total_pages} pages")
            
            return {
                "success": True,
                "message": "Course started successfully",
                "data": {
                    "current_page": first_page,
                    "course_session": {
                        "id": str(uuid.uuid4()),
                        "user_id": user_id,
                        "course_id": course_id,
                        "current_page_index": 0,
                        "completed": False,
                        "started_at": datetime.utcnow().isoformat()
                    }
                }
            }
        except Exception as e:
            logger.error(f"Failed to start course: {e}")
            return {
                "success": False,
                "message": f"Failed to start course: {str(e)}"
            }
    
    async def navigate_course_page(self, user_id: str, course_id: str, page_index: int) -> Dict[str, Any]:
        """Navigate to a specific course page - only from database"""
        try:
            # First check if course exists in database
            course_result = self.supabase.table('courses').select('*').eq('id', course_id).execute()
            if not course_result.data:
                logger.error(f"Course not found in database: {course_id}")
                return {
                    "success": False,
                    "message": f"Course not found: {course_id}. Please ensure the course is properly registered."
                }
            
            # Get the page from database (no fallback)
            page = await self._get_course_page_from_db(course_id, page_index)
            if not page:
                logger.error(f"Page {page_index} not found for course: {course_id}")
                return {
                    "success": False,
                    "message": f"Page {page_index} not found. Please ensure the course is properly registered."
                }
            
            total_pages = await self._get_total_pages(course_id)
            is_last_page = page_index == (total_pages - 1)
            
            logger.info(f"Successfully loaded page {page_index + 1} of {total_pages} for course {course_id}")
            
            return {
                "success": True,
                "message": "Page loaded successfully",
                "data": {
                    "current_page": page
                },
                "total_pages": total_pages,
                "is_last_page": is_last_page
            }
        except Exception as e:
            logger.error(f"Failed to navigate course page: {e}")
            return {
                "success": False,
                "message": f"Failed to load page: {str(e)}"
            }
    
    async def _get_course_page_from_db(self, course_id: str, page_index: int) -> Optional[Dict[str, Any]]:
        """Get course page from database only - no fallback content"""
        try:
            logger.info(f"🔍 Fetching page {page_index} for course {course_id} from database")
            
            # First check if course exists
            course_check = self.supabase.table('courses').select('id').eq('id', course_id).execute()
            if not course_check.data:
                logger.error(f"❌ Course {course_id} not found in courses table")
                return None
            
            logger.info(f"✅ Course {course_id} exists in database")
            
            # Check if course_pages table has any pages for this course
            pages_check = self.supabase.table('course_pages').select('id, page_index').eq('course_id', course_id).execute()
            logger.info(f"📊 Found {len(pages_check.data) if pages_check.data else 0} pages for course {course_id}")
            
            if pages_check.data:
                page_indices = [p['page_index'] for p in pages_check.data]
                logger.info(f"📋 Available page indices: {sorted(page_indices)}")
            
            # Query for specific page
            page_result = self.supabase.table('course_pages').select('*').eq('course_id', course_id).eq('page_index', page_index).execute()
            
            logger.info(f"🔍 Page query result: {len(page_result.data) if page_result.data else 0} rows")
            
            if not page_result.data:
                logger.error(f"❌ Page {page_index} not found for course {course_id}")
                return None
                
            page = page_result.data[0]
            # Parse quiz_data if present and is a string
            if page.get('page_type') == 'quiz' and page.get('quiz_data'):
                if isinstance(page['quiz_data'], str):
                    try:
                        page['quiz_data'] = json.loads(page['quiz_data'])
                        logger.info(f"✅ Quiz data parsed successfully for page {page_index}")
                    except Exception as parse_error:
                        logger.error(f"❌ Failed to parse quiz_data for page {page_index}: {parse_error}")
                        pass
            
            logger.info(f"✅ Page {page_index} found: {page.get('title', 'No title')} (type: {page.get('page_type', 'unknown')})")
            
            return page
            
        except Exception as e:
            logger.error(f"❌ Failed to get course page from DB: {e}")
            logger.error(f"🚨 Error details: {type(e).__name__}: {str(e)}")
            return None
    
    async def submit_course_quiz(self, user_id: str, course_id: str, page_index: int, selected_option: str, correct: bool) -> Dict[str, Any]:
        """Submit a quiz answer for a course page"""
        try:
            # Get current page
            page_result = self.supabase.table('course_pages').select('*').eq('course_id', course_id).eq('page_index', page_index).execute()
            if not page_result.data:
                raise ValueError(f"Page not found: {page_index}")
            
            current_page = page_result.data[0]
            if current_page['page_type'] != 'quiz':
                raise ValueError(f"Page {page_index} is not a quiz page")
            
            # Parse quiz_data if it's a string
            quiz_data = current_page.get('quiz_data', {})
            if isinstance(quiz_data, str):
                try:
                    quiz_data = json.loads(quiz_data)
                except Exception as parse_error:
                    logger.error(f"Failed to parse quiz_data for page {page_index}: {parse_error}")
                    quiz_data = {}
            
            explanation = quiz_data.get('explanation', 'Good job!') if isinstance(quiz_data, dict) else 'Good job!'
            
            # Update quiz answers in session (create session if it doesn't exist)
            session_result = self.supabase.table('user_course_sessions').select('quiz_answers').eq('user_id', user_id).eq('course_id', course_id).execute()
            if session_result.data:
                # Update existing session
                quiz_answers = session_result.data[0].get('quiz_answers', {})
                quiz_answers[str(page_index)] = {
                    'selected_option': selected_option,
                    'correct': correct,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                self.supabase.table('user_course_sessions').update({
                    'quiz_answers': quiz_answers,
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('user_id', user_id).eq('course_id', course_id).execute()
            else:
                # Create new session
                quiz_answers = {
                    str(page_index): {
                        'selected_option': selected_option,
                        'correct': correct,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                }
                
                self.supabase.table('user_course_sessions').insert({
                    'user_id': user_id,
                    'course_id': course_id,
                    'current_page_index': page_index,
                    'completed': False,
                    'quiz_answers': quiz_answers,
                    'started_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }).execute()
            
            # ALSO save to centralized quiz_responses table
            try:
                # Get course details for topic
                course_result = self.supabase.table('courses').select('title, topic').eq('id', course_id).execute()
                course_topic = course_result.data[0].get('topic', 'General Finance') if course_result.data else 'General Finance'
                
                quiz_response_data = {
                    'user_id': user_id,
                    'quiz_id': f'course_quiz_{course_id}_{page_index}_{datetime.utcnow().timestamp()}',
                    'topic': course_topic,
                    'selected': selected_option,
                    'correct': correct,
                    'quiz_type': 'course',
                    'score': 100.0 if correct else 0.0,
                    'course_id': course_id,
                    'page_index': page_index,
                    'question_data': quiz_data,
                    'correct_answer': quiz_data.get('correct_answer', '') if isinstance(quiz_data, dict) else '',
                    'explanation': explanation
                }
                
                self.supabase.table('quiz_responses').insert(quiz_response_data).execute()
                logger.info(f"Course quiz response saved to centralized quiz_responses for user {user_id}, course {course_id}, page {page_index}")
                
            except Exception as e:
                logger.warning(f"Failed to save course quiz to centralized quiz_responses: {e}")
                # Don't fail the main request if centralized save fails
            
            # Get next page if available
            next_page = None
            total_pages = await self._get_total_pages(course_id)
            
            if page_index + 1 < total_pages:
                next_page_result = self.supabase.table('course_pages').select('*').eq('course_id', course_id).eq('page_index', page_index + 1).execute()
                if next_page_result.data:
                    next_page_data = next_page_result.data[0]
                    
                    # Parse quiz_data if present and is a string
                    quiz_data = next_page_data.get('quiz_data')
                    if quiz_data and isinstance(quiz_data, str):
                        try:
                            quiz_data = json.loads(quiz_data)
                        except Exception as parse_error:
                            logger.error(f"Failed to parse quiz_data for next page: {parse_error}")
                            quiz_data = None
                    
                    next_page = {
                        'id': next_page_data['id'],
                        'page_index': next_page_data['page_index'],
                        'title': next_page_data['title'],
                        'content': next_page_data['content'],
                        'page_type': next_page_data['page_type'],
                        'quiz_data': quiz_data,
                        'total_pages': total_pages  # Include total pages for proper numbering
                    }
                else:
                    logger.warning(f"No next page found at index {page_index + 1}")
            else:
                logger.info(f"No next page available - current page {page_index} is the last page (total: {total_pages})")
            
            # Log course progress to Google Sheets
            try:
                # Get course details for logging
                course_result = self.supabase.table('courses').select('title').eq('id', course_id).execute()
                course_name = course_result.data[0]['title'] if course_result.data else 'Unknown Course'
                
                # Get session_id from user_course_sessions or use a generated one
                session_result = self.supabase.table('user_course_sessions').select('id').eq('user_id', user_id).eq('course_id', course_id).execute()
                session_id = str(session_result.data[0]['id']) if session_result.data else f"{user_id}_{course_id}"
                
                progress_data = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "course_id": course_id,
                    "course_name": course_name,
                    "page_number": page_index + 1,  # Convert to 1-based
                    "total_pages": total_pages,
                    "completed": False  # Quiz page completion, not full course
                }
                self.sheets_service.log_course_progress(progress_data)
                
            except Exception as e:
                logger.warning(f"Failed to log course progress to Google Sheets: {e}")
                # Don't fail the main request if logging fails
            
            return {
                'success': True,
                'message': f"Quiz answer submitted successfully",
                'data': {
                    'course_id': course_id,
                    'page_index': page_index
                },
                'correct': correct,
                'explanation': explanation,
                'next_page': next_page
            }
            
        except Exception as e:
            logger.error(f"Failed to submit course quiz: {e}")
            raise
    
    async def complete_course(self, user_id: str, course_id: str) -> Dict[str, Any]:
        """Complete a course for a user"""
        try:
            # Get course details
            course_result = self.supabase.table('courses').select('*').eq('id', course_id).execute()
            if not course_result.data:
                raise ValueError(f"Course not found: {course_id}")
            
            course = course_result.data[0]
            
            # Get session details
            session_result = self.supabase.table('user_course_sessions').select('*').eq('user_id', user_id).eq('course_id', course_id).execute()
            if not session_result.data:
                raise ValueError(f"Course session not found")
            
            session = session_result.data[0]
            quiz_answers = session.get('quiz_answers', {})
            
            # Calculate completion summary
            total_quizzes = len([p for p in quiz_answers.values() if p.get('correct') is not None])
            correct_answers = len([p for p in quiz_answers.values() if p.get('correct')])
            score = (correct_answers / total_quizzes * 100) if total_quizzes > 0 else 0
            
            # Update session as completed
            self.supabase.table('user_course_sessions').update({
                'completed': True,
                'completed_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }).eq('user_id', user_id).eq('course_id', course_id).execute()
            
            # Log course completion to Google Sheets
            try:
                total_pages = await self._get_total_pages(course_id)
                session_id = str(session.get('id', f"{user_id}_{course_id}"))
                
                progress_data = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "course_id": course_id,
                    "course_name": course['title'],
                    "page_number": total_pages,  # Final page
                    "total_pages": total_pages,
                    "completed": True  # Full course completion
                }
                self.sheets_service.log_course_progress(progress_data)
                
            except Exception as e:
                logger.warning(f"Failed to log course completion to Google Sheets: {e}")
                # Don't fail the main request if logging fails
            
            completion_summary = {
                'course_title': course['title'],
                'total_quizzes': total_quizzes,
                'correct_answers': correct_answers,
                'score': score,
                'completed_at': datetime.utcnow().isoformat()
            }
            
            return {
                'success': True,
                'message': f"Course '{course['title']}' completed successfully!",
                'data': {
                    'course_id': course_id,
                    'completion_summary': completion_summary
                },
                'completion_summary': completion_summary
            }
            
        except Exception as e:
            logger.error(f"Failed to complete course: {e}")
            raise
    
    async def _get_total_pages(self, course_id: str) -> int:
        """Get total number of pages for a course"""
        try:
            logger.info(f"🔍 Getting total pages for course {course_id}")
            result = self.supabase.table('course_pages').select('page_index').eq('course_id', course_id).execute()
            total_pages = len(result.data)
            logger.info(f"📊 Total pages found: {total_pages} for course {course_id}")
            if result.data:
                page_indices = [p['page_index'] for p in result.data]
                logger.info(f"📋 Page indices: {sorted(page_indices)}")
            return total_pages
        except Exception as e:
            logger.error(f"❌ Failed to get total pages: {e}")
            return 0 

    async def track_course_progress(self, user_id: str, course_name: str, tabs_completed: int = 1, level: str = "easy") -> bool:
        """
        Track course progress when user completes sections/tabs
        
        Args:
            user_id: User ID
            course_name: Name of the course
            tabs_completed: Number of tabs/sections completed (default 1)
            level: Course level (easy, medium, hard)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from app.services.user_service import UserService
            user_service = UserService()
            
            # Update course progress
            success = await user_service.update_course_progress(
                user_id=user_id,
                course_name=course_name,
                questions_taken=0,  # No new questions
                score=None,  # Keep existing score
                tabs_completed=tabs_completed,  # Update tabs completed
                level=level  # Update level
            )
            
            if success:
                logger.info(f"Course progress tracked for user {user_id}, course {course_name}")
            else:
                logger.warning(f"Failed to track course progress for user {user_id}, course {course_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error tracking course progress: {e}")
            return False

    async def complete_course_section(self, user_id: str, course_name: str, section_name: str, level: str = "easy") -> bool:
        """
        Mark a course section as completed
        
        Args:
            user_id: User ID
            course_name: Name of the course
            section_name: Name of the completed section
            level: Course level (easy, medium, hard)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Track the progress
            success = await self.track_course_progress(user_id, course_name, tabs_completed=1, level=level)
            
            if success:
                logger.info(f"Course section '{section_name}' completed for user {user_id} in course {course_name}")
                
                # You can add additional logic here like:
                # - Sending notifications
                # - Updating achievements
                # - Logging to analytics
                
            return success
            
        except Exception as e:
            logger.error(f"Error completing course section: {e}")
            return False 