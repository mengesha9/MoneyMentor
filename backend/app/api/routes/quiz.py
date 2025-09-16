import asyncio
from app.services.background_sync_service import background_sync_service
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any, List
import logging
import uuid

from app.models.schemas import QuizRequest, QuizResponse, QuizAttempt, QuizAttemptResponse, QuizSubmission, QuizSubmissionBatch, CourseRecommendation
from app.agents.crew import money_mentor_crew
from app.services.quiz_service import QuizService
from app.services.google_sheets_service import GoogleSheetsService
from app.services.content_service import ContentService
from app.services.course_service import CourseService
from app.services.ai_course_service import AICourseService
from app.core.database import get_supabase
from app.core.auth import get_current_active_user
from datetime import datetime
from app.utils.session import get_session, create_session
from app.utils.user_validation import require_authenticated_user_id, sanitize_user_id_for_logging
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from app.core.config import settings
import json

logger = logging.getLogger(__name__)
router = APIRouter()

# Note: Exception handlers should be added to the main FastAPI app, not to APIRouter
# The enhanced error handling is now in the function-level try-catch blocks

# Initialize Google Sheets service
google_sheets_service = GoogleSheetsService()

# Initialize LLM for course generation
course_llm = ChatOpenAI(
    model=settings.OPENAI_MODEL_GPT4_MINI,
    api_key=settings.OPENAI_API_KEY,
    temperature=0.7
)

@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(
    request: QuizRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Generate a quiz using CrewAI quiz master agent"""
    
    # 🔍 DEBUG: Print quiz generation request data
    print("=" * 80)
    print("QUIZ GENERATION - INCOMING REQUEST DATA")
    print("=" * 80)
    print(f"📋 Quiz Type: {request.quiz_type}")
    print(f"Topic: {request.topic}")
    print(f"📊 Difficulty: {request.difficulty}")
    print(f"🆔 Session ID: {request.session_id}")
    print(f"👤 User ID: {current_user['id']}")
    print("=" * 80)
    
    try:
        session = await get_session(request.session_id)
        if not session:
            logger.debug("creating new session✅session✅session✅session✅session✅")
            logger.debug(f"Session ID from request: {request.session_id}")
            logger.debug(f"User ID from token: {current_user['id']}")
            # If session does not exist, create it with the actual user_id
            # Validate user_id is a real UUID from authentication
            validated_user_id = require_authenticated_user_id(current_user["id"], "quiz session creation")
            session = await create_session(
                session_id=request.session_id, 
                user_id=validated_user_id
            )
        chat_history = session.get("chat_history", [])

        quiz_service = QuizService()
        quiz_id = f"quiz_{request.session_id}_{datetime.utcnow().timestamp()}"
        print(f"{chat_history} ✅session✅session✅session✅session✅")
        
        # Check if topic is provided in request to determine quiz type
        if request.topic:
            # Topic provided: generate diagnostic quiz (10 questions) focused on the specific topic
            difficulty = request.difficulty if request.difficulty else "mixed"
            print(f"Generating diagnostic quiz for topic: {request.topic} with difficulty: {difficulty}")
            
            diagnostic_questions = await quiz_service.generate_diagnostic_quiz(topic=request.topic, difficulty=difficulty)
            # Convert to required structure (choices, correct_answer as str, etc.)
            processed_questions = []
            for q in diagnostic_questions:
                processed_questions.append({
                    'question': q.get('question', ''),
                    'choices': q.get('choices', {}),
                    'correct_answer': q.get('correct_answer', ''),
                    'explanation': q.get('explanation', ''),
                    'topic': q.get('topic', ''),  # Include topic for diagnostic quiz
                    'difficulty': q.get('difficulty', difficulty)  # Include difficulty
                })
            
            # 🔍 DEBUG: Print diagnostic quiz response data
            print("=" * 80)
            print("📚 DIAGNOSTIC QUIZ GENERATION RESPONSE")
            print("=" * 80)
            print(f"🆔 Quiz ID: {quiz_id}")
            print(f"📋 Quiz Type: {request.quiz_type}")
            print(f"Topic: {request.topic}")
            print(f"📊 Difficulty: {difficulty}")
            print(f"❓ Number of Questions: {len(processed_questions)}")
            print(f"📝 Questions Generated: {len(diagnostic_questions)}")
            print("=" * 80)
            
            return QuizResponse(
                questions=processed_questions,
                quiz_id=quiz_id,
                quiz_type=request.quiz_type,
                topic=request.topic  # Include topic for diagnostic quiz
            )
        else:
            # No topic provided: generate micro-quiz question about the most recent topic from chat history
            # Extract topic from chat history for micro quiz
            recent_messages = [msg for msg in chat_history if msg.get("role") == "user"]
            if recent_messages:
                topic = quiz_service.extract_topic_from_message(recent_messages[-1].get("content", ""))
            else:
                topic = "General Finance"
            
            questions = await quiz_service.generate_quiz_from_history(
                session_id=request.session_id,
                quiz_type=request.quiz_type.value,
                difficulty=request.difficulty or "medium",
                chat_history=chat_history
            )
            # Only return the first question for micro-quiz
            return QuizResponse(
                questions=questions[:1],
                quiz_id=quiz_id,
                quiz_type=request.quiz_type
                # Don't include topic for micro quiz response
            )
    except Exception as e:
        logger.error(f"Quiz generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate quiz")

@router.post("/submit", response_model=Dict[str, Any])
async def submit_quiz(
    request: Request,  # Add this to access raw request data
    quiz_batch: QuizSubmissionBatch,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Submit one or more quiz responses at once (for both micro and diagnostic quizzes)
    
    For diagnostic quizzes, this endpoint will also generate a personalized course recommendation
    based on the user's performance and identified areas for improvement.
    
    Expected payload:
    {
        "user_id": "string",
        "quiz_type": "micro" or "diagnostic",
        "responses": [
            {
                "quiz_id": "quiz_1",
                "selected_option": "B",
                "correct": true,
                "topic": "Investing"
            },
            ...
        ]
    }
    
    Response for diagnostic quizzes includes:
    {
        "success": true,
        "data": {
            "user_id": "string",
            "quiz_type": "diagnostic",
            "overall_score": 65.0,
            "topic_breakdown": {...},
            "recommended_course_id": "course_id"
        }
    }
    """
    
    try:
        # 🔍 DEBUG: Print incoming request data
        print("=" * 80)
        print("🚀 COURSE GENERATION - INCOMING REQUEST DATA")
        print("=" * 80)
        
        # Log raw request data first
        try:
            body = await request.body()
            print(f"📝 Raw Request Body: {body.decode()}")
        except Exception as e:
            print(f"📝 Raw Request Body: Could not read - {e}")
        
     
        print("\n📝 Individual Quiz Responses:")
        for i, response in enumerate(quiz_batch.responses):
           
            # Check for any extra fields that might cause validation issues
            extra_fields = {k: v for k, v in response.items() if k not in ['quiz_id', 'topic', 'selected_option', 'correct']}
            if extra_fields:
                print(f"    ⚠️ Extra fields: {extra_fields}")
        print("=" * 80)
        
        # 🔍 DEBUG: Validate each response manually to catch any issues
        print("\n🔍 MANUAL VALIDATION:")
        for i, response in enumerate(quiz_batch.responses):
            print(f"  Validating Response {i+1}:")
            
            # Check required fields
            required_fields = ['quiz_id', 'selected_option', 'correct', 'topic']
            for field in required_fields:
                if field not in response:
                    print(f"    ❌ Missing required field: {field}")
                else:
                    print(f"    ✅ {field}: {response[field]} (type: {type(response[field])})")
            
            # Validate selected_option format
            selected = response.get('selected_option')
            if selected and selected not in ['A', 'B', 'C', 'D']:
                print(f"    ❌ Invalid selected_option: {selected} (must be A, B, C, or D)")
            elif selected:
                print(f"    ✅ selected_option: {selected} (valid)")
            
            # Validate correct field is boolean
            correct = response.get('correct')
            if not isinstance(correct, bool):
                print(f"    ❌ Invalid correct field: {correct} (type: {type(correct)}, must be boolean)")
            else:
                print(f"    ✅ correct: {correct} (valid boolean)")
        
        print("=" * 80)
        
        supabase = get_supabase()
        
        # Ensure session exists in database before submitting quiz
        if quiz_batch.session_id:
            try:
                # Check if session exists in database
                session_result = supabase.table("user_sessions").select("session_id").eq("session_id", quiz_batch.session_id).execute()
                if not session_result.data or len(session_result.data) == 0:
                    # Session doesn't exist, create it
                    logger.info(f"Session {quiz_batch.session_id} not found, creating new session")
                    session_data = {
                        "session_id": quiz_batch.session_id,
                        "user_id": current_user["id"],
                        "chat_history": [],
                        "progress": {},
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    supabase.table("user_sessions").insert(session_data).execute()
                    logger.info(f"Created session {quiz_batch.session_id} for quiz submission")
            except Exception as session_error:
                logger.error(f"Failed to ensure session exists: {session_error}")
                # Continue with quiz submission even if session creation fails
        
        # 1. Prepare batch data for quiz_responses table
        quiz_responses_batch = []
        topic_stats = {}  # Track stats for user_progress update
        
        for response in quiz_batch.responses:
            quiz_response_data = {
                "user_id": current_user["id"],  # Use user_id from token
                "quiz_id": response["quiz_id"],
                "topic": response["topic"],
                "selected": response["selected_option"],
                "correct": response["correct"],
                "quiz_type": quiz_batch.quiz_type,
                "score": 100.0 if response["correct"] else 0.0,
                # Add all quiz details for proper storage
                "explanation": response.get("explanation", ""),
                "correct_answer": response.get("correct_answer", ""),
                "question_data": response.get("question_data", {}),
                "session_id": quiz_batch.session_id
            }
            quiz_responses_batch.append(quiz_response_data)
            
            # Track topic statistics
            topic = response["topic"]
            if topic not in topic_stats:
                topic_stats[topic] = {"total": 0, "correct": 0}
            topic_stats[topic]["total"] += 1
            if response["correct"]:
                topic_stats[topic]["correct"] += 1
        
        # 2. Insert all quiz responses in batch
        if quiz_responses_batch:
            supabase.table('quiz_responses').insert(quiz_responses_batch).execute()
        
        # 3. Update user_progress table with aggregated stats
        await _update_user_progress_from_batch(current_user["id"], quiz_batch.quiz_type, topic_stats)
        
        # 4. Log to Google Sheets (for client access)
        if google_sheets_service.service:
            try:
                # Prepare data for Google Sheets (new schema)
                sheets_data = []
                for response in quiz_batch.responses:
                    sheets_data.append({
                        'user_id': current_user["id"],  # Use user_id from token
                        'quiz_id': response["quiz_id"],
                        'topic_tag': response["topic"],  # Updated to topic_tag
                        'selected_option': response["selected_option"],  # Updated to selected_option
                        'correct': response["correct"],
                        'session_id': quiz_batch.session_id or current_user["id"]  # Use session_id if provided
                    })
                
                # Log to Google Sheets
                if len(sheets_data) == 1:
                    google_sheets_service.log_quiz_response(sheets_data[0])
                else:
                    google_sheets_service.log_multiple_responses(sheets_data)
                
                logger.info(f"Quiz responses logged to Google Sheets for user {quiz_batch.user_id}")
                
            except Exception as e:
                logger.error(f"Failed to log to Google Sheets: {e}")
                # Don't fail the entire request if Google Sheets fails
        else:
            logger.warning("Google Sheets service not available - quiz responses not logged to client sheet")
        
        # 5. Calculate overall results
        total_responses = len(quiz_batch.responses)
        correct_responses = sum(1 for r in quiz_batch.responses if r["correct"])
        overall_score = (correct_responses / total_responses * 100) if total_responses > 0 else 0
        
        logger.info(f"Quiz submission(s) successful for user {current_user['id']}: {correct_responses}/{total_responses} correct")
        
        # 6. Generate course recommendation for diagnostic quizzes only
        recommended_course_id = None
        if quiz_batch.quiz_type == "diagnostic":
            # Always create and register a proper course (no random UUID generation)
            try:
                logger.info("Creating course recommendation")
                
            
                
                # Check if user selected a specific course type
                selected_course_type = quiz_batch.selected_course_type
                if selected_course_type:
                    print(f"Selected Course Type: {selected_course_type}")
                
                # Analyze topic breakdown from responses
                print("\n📋 Topic Breakdown Analysis:")
                topic_analysis = {}
                for response in quiz_batch.responses:
                    topic = response.get('topic', 'Unknown')
                    if topic not in topic_analysis:
                        topic_analysis[topic] = {'total': 0, 'correct': 0}
                    topic_analysis[topic]['total'] += 1
                    if response.get('correct', False):
                        topic_analysis[topic]['correct'] += 1
                
                for topic, stats in topic_analysis.items():
                    topic_score = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
                    print(f"  🎯 {topic}: {stats['correct']}/{stats['total']} correct ({topic_score:.1f}%)")
                
                # Determine course level based on score
                if overall_score >= 80:
                    course_level = "Advanced"
                elif overall_score >= 60:
                    course_level = "Intermediate"
                else:
                    course_level = "Beginner"
                
                # Use selected course type if available, otherwise derive from quiz performance
                if selected_course_type:
                    # Map course keys to human-readable titles
                    course_type_mapping = {
                        'money-goals-mindset': 'Money, Goals and Mindset',
                        'budgeting-saving': 'Budgeting and Saving',
                        'college-planning-saving': 'College Planning and Saving',
                        'earning-income-basics': 'Earning and Income Basics'
                    }
                    focus_topic = course_type_mapping.get(selected_course_type, selected_course_type)
                    print(f"Using selected course type: {focus_topic}")
                else:
                    print(f"No course type selected, deriving topic from quiz responses")
                    # Derive topic from quiz responses if no course type selected
                    if quiz_batch.responses and len(quiz_batch.responses) > 0:
                        # Get the most common topic from responses
                        topic_counts = {}
                        for response in quiz_batch.responses:
                            topic = response.get('topic', 'Unknown')
                            topic_counts[topic] = topic_counts.get(topic, 0) + 1
                        
                        # Find the most common topic
                        if topic_counts:
                            most_common_topic = max(topic_counts, key=topic_counts.get)
                            focus_topic = most_common_topic
                            print(f"Derived topic from quiz responses: {focus_topic}")
                        else:
                            focus_topic = "General Finance"
                            print(f"No topics found, using default: {focus_topic}")
                    else:
                        focus_topic = "General Finance"
                        print(f"No responses available, using default: {focus_topic}")
           
                
                # Generate course using AI service
                print("🤖 Starting AI course generation...")
                ai_course_service = AICourseService()
                ai_generated_course = await ai_course_service.generate_course(
                    selected_course_type=selected_course_type,
                    quiz_responses=quiz_batch.responses,
                    overall_score=overall_score,
                    user_id=current_user['id']
                )
            
                # Convert AI course to course data format for database storage
                course_data = {
                    "title": ai_generated_course.title,
                    "module": f"{focus_topic} Fundamentals",
                    "track": "High School",
                    "estimated_length": "10 pages, up to 500 characters each",
                    "lesson_overview": f"This AI-generated course on {focus_topic} is personalized to your {course_level.lower()} level based on your {overall_score}% diagnostic score.",
                    "learning_objectives": [
                        f"Master key {focus_topic.lower()} concepts",
                        f"Apply knowledge to real financial decisions",
                        f"Build confidence in {focus_topic.lower()} planning"
                    ],
                    "core_concepts": [
                        {
                            "title": f"Personalized {focus_topic} Learning",
                            "explanation": f"This course is tailored to your {course_level.lower()} level and focuses on areas where you can improve based on your diagnostic results.",
                            "metaphor": "Think of it like having a personal tutor who knows exactly what you need to learn!",
                            "quick_challenge": f"What's one {focus_topic.lower()} concept you want to understand better?"
                        }
                    ],
                    "key_terms": [
                        {
                            "term": focus_topic,
                            "definition": f"The practice of managing {focus_topic.lower()} effectively",
                            "example": f"Creating a {focus_topic.lower()} plan for your monthly expenses"
                        }
                    ],
                    "real_life_scenarios": [
                        {
                            "title": f"Your {focus_topic} Journey",
                            "narrative": f"Based on your diagnostic results, this course will help you build a strong foundation in {focus_topic.lower()} concepts."
                        }
                    ],
                    "mistakes_to_avoid": [
                        f"Not practicing {focus_topic.lower()} concepts regularly",
                        f"Ignoring the importance of {focus_topic.lower()} in daily life"
                    ],
                    "action_steps": [
                        f"Complete all 10 pages of this course",
                        f"Apply what you learn to real situations",
                        f"Track your progress in {focus_topic.lower()}"
                    ],
                    "summary": f"You've completed a personalized course on {focus_topic} designed specifically for your {course_level.lower()} level. Keep practicing and building on this foundation!",
                    "reflection_prompt": f"What's the most important thing you learned about {focus_topic.lower()} today?",
                    "sample_quiz": [
                        {
                            "question": f"What is the main benefit of understanding {focus_topic}?",
                            "options": {
                                "a": "It's required for school",
                                "b": "It helps make better financial decisions",
                                "c": "It's only important for adults",
                                "d": "It doesn't matter much"
                            },
                            "correct_answer": "b",
                            "explanation": f"Understanding {focus_topic.lower()} concepts helps you make informed decisions about your money."
                        }
                    ],
                    "course_level": course_level.lower(),
                    "why_recommended": f"Based on your {overall_score}% diagnostic score and your selection of {focus_topic}. This AI-generated course is personalized to your knowledge level and interests.",
                    "has_quiz": True,
                    "topic": focus_topic,
                    # AI course specific fields
                    "page_structure": "ai_generated",
                    "target_audience": f"{course_level.lower()} level learners",
                    "learning_style": "personalized_and_adaptive",
                    "estimated_pages": len(ai_generated_course.pages),
                    "page_focus": "ai_optimized",
                    "total_pages": len(ai_generated_course.pages)
                }
                
                # 🔍 DEBUG: Print generated course data
               
                # Add AI-generated pages to course_data for page generation (not for database storage)
                course_data_with_pages = course_data.copy()
                course_data_with_pages["ai_generated_pages"] = ai_generated_course.pages
                
                course_service = CourseService()
                recommended_course_id = await course_service.register_course(course_data_with_pages)
                logger.info(f"Course registered successfully: {recommended_course_id}")
                
                print(f"✅ Course Registration Result:")
                print(f"  🆔 Course ID: {recommended_course_id}")
                print(f"  📊 Status: Success")
                
                # Verify the course was actually registered by checking database
                try:
                    print("🔍 Verifying course registration in database...")
                    verification_result = supabase.table('courses').select('id').eq('id', recommended_course_id).execute()
                    if verification_result.data:
                        logger.info(f"Course registration verified: {recommended_course_id}")
                        print(f"✅ Database Verification: SUCCESS")
                        print(f"  🆔 Verified Course ID: {recommended_course_id}")
                    else:
                        logger.error(f"Course registration verification failed: {recommended_course_id}")
                        print(f"❌ Database Verification: FAILED")
                        print(f"  🆔 Course ID not found: {recommended_course_id}")
                except Exception as verify_error:
                    logger.error(f"Failed to verify course registration: {verify_error}")
                    print(f"❌ Database Verification: ERROR")
                    print(f"  🚨 Error: {verify_error}")
                
                print("=" * 80)
                
                # Store AI-generated course data for immediate frontend use
                ai_course_data = {
                    "course_id": recommended_course_id,
                    "title": ai_generated_course.title,
                    "pages": ai_generated_course.pages,
                    "total_pages": len(ai_generated_course.pages),  # Use actual number of pages generated
                    "course_level": course_level.lower(),
                    "focus_topic": focus_topic
                }
                
            except Exception as course_error:
                logger.error(f"Failed to create course: {course_error}")
              
                # Try to create a minimal test course to see if database is working
                try:
                    logger.info("Attempting to create minimal test course")
                    course_service = CourseService()
                    
                    # Test basic database connection first
                    try:
                        test_result = supabase.table('courses').select('id').limit(1).execute()
                        logger.info("Database connection test successful")
                        db_available = True
                    except Exception as db_test_error:
                        if "does not exist" in str(db_test_error):
                            logger.warning("Courses table does not exist, using fallback mode")
                            db_available = False
                        else:
                            logger.error(f"Database connection test failed: {db_test_error}")
                            db_available = True  # Assume available for other errors
                    
                    if db_available:
                        # Try to insert a very basic course
                        basic_course_data = {
                            'id': str(uuid.uuid4()),
                            'title': 'Test Course',
                            'module': 'Test Module',
                            'track': 'High School',
                            'estimated_length': '2,000-2,500 words',
                            'lesson_overview': 'Test overview',
                            'learning_objectives': [],
                            'core_concepts': [],
                            'key_terms': [],
                            'real_life_scenarios': [],
                            'mistakes_to_avoid': [],
                            'action_steps': [],
                            'summary': 'Test summary',
                            'reflection_prompt': 'Test reflection',
                            'course_level': 'beginner',
                            'why_recommended': 'Test recommendation',
                            'has_quiz': True,
                            'topic': 'Test',
                            'created_at': datetime.utcnow().isoformat(),
                            'updated_at': datetime.utcnow().isoformat()
                        }
                        
                        # Try direct database insertion
                        try:
                            direct_result = supabase.table('courses').insert(basic_course_data).execute()
                            logger.info(f"Direct database insertion successful: {basic_course_data['id']}")
                            recommended_course_id = basic_course_data['id']
                        except Exception as direct_error:
                            logger.error(f"Direct database insertion failed: {direct_error}")
                            # Try with CourseService as last resort
                            test_course_data = {
                                "title": "Test Course",
                                "module": "Test Module",
                                "track": "High School",
                                "estimated_length": "2,000-2,500 words",
                                "lesson_overview": "Test overview",
                                "learning_objectives": [],
                                "core_concepts": [],
                                "key_terms": [],
                                "real_life_scenarios": [],
                                "mistakes_to_avoid": [],
                                "action_steps": [],
                                "summary": "Test summary",
                                "reflection_prompt": "Test reflection",
                                "course_level": "beginner",
                                "why_recommended": "Test recommendation",
                                "has_quiz": True,
                                "topic": "Test"
                            }
                            test_course_id = await course_service.register_course(test_course_data)
                            logger.info(f"Test course created successfully: {test_course_id}")
                            recommended_course_id = test_course_id
                    else:
                        # Database not available, create a fallback course ID
                        logger.warning("Database not available, creating fallback course ID")
                        recommended_course_id = str(uuid.uuid4())
                        
                except Exception as test_error:
                    logger.error(f"Test course creation also failed: {test_error}")
                    # Create a fallback course ID
                    recommended_course_id = str(uuid.uuid4())
        
        # 7. Prepare Google Sheets URL for user access
        google_sheets_url = "https://docs.google.com/spreadsheets/d/1dj0l7UBaG-OkQKtSfrlf_7uDdhJu7g65OapGeKgC6bs/edit?gid=1325423234#gid=1325423234"
        
        # 8. Prepare response data
        response_data = {
            "user_id": quiz_batch.user_id,
            "quiz_type": quiz_batch.quiz_type,
            "total_responses": total_responses,
            "correct_responses": correct_responses,
            "overall_score": overall_score,
            "topic_breakdown": topic_stats,
            "google_sheets_logged": google_sheets_service.service is not None,
            "google_sheets_url": google_sheets_url,
            "recommended_course_id": recommended_course_id,
            "ai_generated_course": ai_course_data if 'ai_course_data' in locals() else None
        }
        
      
        
        # Log AI-generated course data if available
        if 'ai_generated_course' in response_data and response_data['ai_generated_course']:
            print(f"🤖 AI Generated Course: {response_data['ai_generated_course']}")
        else:
            print("🤖 AI Generated Course: None")
        
        print("=" * 80)
        
        # 7. Trigger background sync to Google Sheets after successful quiz submission (non-blocking)
        try:
            # Use the existing background sync service asynchronously
            asyncio.create_task(background_sync_service.force_sync_now())
            logger.info(f"Background sync triggered for user {current_user['id']} after quiz submission")
            
        except Exception as e:
            logger.warning(f"Failed to trigger background sync after quiz submission: {e}")
            # Don't fail the entire request if sync fails
        
        return {
            "success": True,
            "message": f"Quiz submission(s) successful: {correct_responses}/{total_responses} correct",
            "data": response_data
        }
        
    except Exception as e:
        logger.error(f"Failed to submit quiz responses: {e}")
        
        # 🔍 ENHANCED ERROR REPORTING
     
        # If it's a validation error, show the expected format
        if "validation error" in str(e).lower() or "422" in str(e):
            print("\n📋 EXPECTED REQUEST FORMAT:")
            print("""
{
    "user_id": "string (UUID)",
    "quiz_type": "diagnostic" or "micro",
    "session_id": "string (UUID)",
    "responses": [
        {
            "quiz_id": "string",
            "selected_option": "A", "B", "C", or "D",
            "correct": true or false,
            "topic": "string"
        }
    ]
}
            """)
        
        
        # Return a more helpful error response
        if "validation error" in str(e).lower() or "422" in str(e):
            raise HTTPException(
                status_code=422, 
                detail={
                    "error": "Validation Error",
                    "message": "Request data format is invalid",
                    "received_data": {
                        "quiz_type": getattr(quiz_batch, 'quiz_type', 'NOT_PROVIDED'),
                        "user_id": getattr(quiz_batch, 'user_id', 'NOT_PROVIDED'),
                        "session_id": getattr(quiz_batch, 'session_id', 'NOT_PROVIDED'),
                        "responses_count": len(getattr(quiz_batch, 'responses', [])),
                        "responses_sample": getattr(quiz_batch, 'responses', [])[:2] if getattr(quiz_batch, 'responses', []) else []
                    },
                    "expected_format": {
                        "user_id": "string (UUID)",
                        "quiz_type": "diagnostic or micro",
                        "session_id": "string (UUID)",
                        "responses": [
                            {
                                "quiz_id": "string",
                                "selected_option": "A, B, C, or D",
                                "correct": "boolean (true/false)",
                                "topic": "string"
                            }
                        ]
                    },
                    "validation_errors": str(e)
                }
            )
        else:
            raise HTTPException(status_code=500, detail=f"Failed to submit quiz responses: {str(e)}")

async def _update_user_progress_from_batch(user_id: str, quiz_type: str, topic_stats: Dict[str, Dict[str, int]]) -> bool:
    """
    Update user_progress table based on batch quiz results
    
    Args:
        user_id: User identifier
        quiz_type: Type of quiz
        topic_stats: Dictionary with topic statistics {"topic": {"total": X, "correct": Y}}
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        supabase = get_supabase()
        
        # Get current progress
        result = supabase.table('user_progress').select('*').eq('user_id', user_id).execute()
        current_progress = result.data[0] if result.data else {}
        
        # Update quiz scores
        quiz_scores = current_progress.get('quiz_scores', {})
        if quiz_type not in quiz_scores:
            quiz_scores[quiz_type] = {'total': 0, 'correct': 0, 'topics': {}}
        
        # Update topics covered
        topics_covered = current_progress.get('topics_covered', {})
        
        # Process each topic from the batch
        for topic, stats in topic_stats.items():
            total = stats["total"]
            correct = stats["correct"]
            
            # Update quiz scores for this quiz type
            quiz_scores[quiz_type]['total'] += total
            quiz_scores[quiz_type]['correct'] += correct
            
            # Update topic-specific scores
            if topic not in quiz_scores[quiz_type]['topics']:
                quiz_scores[quiz_type]['topics'][topic] = {'total': 0, 'correct': 0}
            
            quiz_scores[quiz_type]['topics'][topic]['total'] += total
            quiz_scores[quiz_type]['topics'][topic]['correct'] += correct
            
            # Update topics covered
            if topic not in topics_covered:
                topics_covered[topic] = {
                    'first_seen': datetime.utcnow().isoformat(),
                    'total_attempts': 0,
                    'correct_attempts': 0
                }
            
            topics_covered[topic]['total_attempts'] += total
            topics_covered[topic]['correct_attempts'] += correct
        
        # Calculate overall score for this quiz type
        total_attempts = quiz_scores[quiz_type]['total']
        correct_attempts = quiz_scores[quiz_type]['correct']
        overall_score = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
        
        # Update strengths and weaknesses based on performance
        strengths = []
        weaknesses = []
        recommendations = []
        
        for topic_name, topic_data in topics_covered.items():
            topic_accuracy = topic_data['correct_attempts'] / topic_data['total_attempts'] if topic_data['total_attempts'] > 0 else 0
            if topic_accuracy >= 0.7:  # 70% or higher
                strengths.append(topic_name)
            elif topic_accuracy < 0.5:  # Below 50%
                weaknesses.append(topic_name)
                recommendations.append(f"Review {topic_name} concepts")
        
        # Prepare progress data
        progress_data = {
            'user_id': user_id,
            'quiz_scores': quiz_scores,
            'topics_covered': topics_covered,
            'last_activity': datetime.utcnow().isoformat(),
            'last_quiz_type': quiz_type,
            'last_quiz_score': overall_score,
            'last_quiz_date': datetime.utcnow().isoformat(),
            'strengths': strengths,
            'weaknesses': weaknesses,
            'recommendations': recommendations,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Upsert to database
        supabase.table('user_progress').upsert(progress_data).execute()
        
        logger.info(f"User progress updated for user {user_id} from batch submission")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update user progress from batch: {e}")
        return False

def _enrich_quiz_data(quiz_history: list) -> list:
    """Helper function to enrich quiz data with parsed question_data and display titles"""
    processed_quiz_history = []
    
    for quiz in quiz_history:
        # Parse question_data if it's a string
        question_data = quiz.get('question_data', {})
        if isinstance(question_data, str):
            try:
                import json
                question_data = json.loads(question_data)
            except (json.JSONDecodeError, TypeError):
                question_data = {}
        
        # Extract question text for display
        question_text = ""
        if question_data and isinstance(question_data, dict):
            question_text = question_data.get('question', '')
        
        # Only include quizzes with valid question text
        if question_text and question_text.strip():
            # Use topic as fallback, then quiz_id if no question text
            display_title = question_text or quiz.get('topic', '') or quiz.get('quiz_id', 'Unknown Quiz')
            
            # Create enriched quiz record
            enriched_quiz = {
                **quiz,  # Keep all original fields
                'question_data': question_data,
                'display_title': display_title,
                'question_text': question_text,
                # Ensure these fields are properly set
                'topic': quiz.get('topic', '') or (question_data.get('topic', '') if question_data else ''),
                'explanation': quiz.get('explanation', '') or (question_data.get('explanation', '') if question_data else ''),
                'correct_answer': quiz.get('correct_answer', '') or (question_data.get('correct_answer', '') if question_data else '')
            }
            
            processed_quiz_history.append(enriched_quiz)
    
    return processed_quiz_history

@router.get("/history")
async def get_quiz_history(current_user: dict = Depends(get_current_active_user)):
    """Get user's quiz history and performance from centralized storage"""
    try:
        supabase = get_supabase()
        
        # Get quiz history for the user from centralized quiz_responses table
        result = supabase.table('quiz_responses').select('*').eq('user_id', current_user["id"]).order('created_at', desc=True).execute()
        
        # Process and enrich quiz data
        quiz_history = result.data if result.data else []
        processed_quiz_history = _enrich_quiz_data(quiz_history)
        
        # Group by quiz type for better organization
        quiz_by_type = {
            'course': [],
            'diagnostic': [],
            'micro': []  # Session-specific quizzes are micro quizzes
        }
        
        for quiz in processed_quiz_history:
            quiz_type = quiz.get('quiz_type', 'micro')
            if quiz_type in quiz_by_type:
                quiz_by_type[quiz_type].append(quiz)
            else:
                quiz_by_type['micro'].append(quiz)
        
        return {
            "user_id": current_user["id"],
            "quiz_history": processed_quiz_history,
            "quiz_by_type": quiz_by_type,
            "total_quizzes": len(processed_quiz_history),
            "course_quizzes": len(quiz_by_type['course']),
            "diagnostic_quizzes": len(quiz_by_type['diagnostic']),
            "micro_quizzes": len(quiz_by_type['micro'])  # Includes both micro and session quizzes
        }
        
    except Exception as e:
        logger.error(f"Quiz history retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get quiz history")

@router.get("/history/session/{session_id}")
async def get_session_quiz_history(
    session_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get micro quiz history for a specific session from centralized storage"""
    try:
        supabase = get_supabase()
        
        # Get micro quiz history for the specific session by filtering quiz_id pattern
        # Quiz IDs are generated as: quiz_{session_id}_{timestamp}
        result = supabase.table('quiz_responses').select('*').like('quiz_id', f'quiz_{session_id}_%').eq('user_id', current_user["id"]).eq('quiz_type', 'micro').order('created_at', desc=True).execute()
        
        # Process and enrich quiz data (same as main history endpoint)
        quiz_history = result.data if result.data else []
        processed_quiz_history = _enrich_quiz_data(quiz_history)
        
        return {
            "session_id": session_id,
            "user_id": current_user["id"],
            "quiz_history": processed_quiz_history,
            "total_quizzes": len(processed_quiz_history),
            "quiz_type": "micro"  # Clarify that these are micro quizzes
        }
        
    except Exception as e:
        logger.error(f"Session micro quiz history retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get session micro quiz history")

@router.get("/progress/session/{session_id}")
async def get_session_quiz_progress(
    session_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get session-specific quiz progress for the quiz tracker button"""
    try:
        supabase = get_supabase()
        
        # Get micro quiz history for the specific session by filtering quiz_id pattern
        # Quiz IDs are generated as: quiz_{session_id}_{timestamp}
        # PERFORMANCE FIX: Wrap in asyncio.to_thread for non-blocking operation
        result = await asyncio.to_thread(
            lambda: supabase.table('quiz_responses').select('*').like('quiz_id', f'quiz_{session_id}_%').eq('user_id', current_user["id"]).eq('quiz_type', 'micro').execute()
        )
        
        quiz_responses = result.data if result.data else []
        
        # Filter out quizzes without valid question data (same logic as history display)
        valid_quiz_responses = []
        for quiz in quiz_responses:
            # Parse question_data if it's a string
            question_data = quiz.get('question_data', {})
            if isinstance(question_data, str):
                try:
                    import json
                    question_data = json.loads(question_data)
                except (json.JSONDecodeError, TypeError):
                    question_data = {}
            
            # Only include quizzes with valid question text
            question_text = question_data.get('question', '') if question_data else ''
            if question_text and question_text.strip():
                valid_quiz_responses.append(quiz)
        
        total_quizzes = len(valid_quiz_responses)
        correct_answers = sum(1 for quiz in valid_quiz_responses if quiz.get('correct', False))
        
        return {
            "session_id": session_id,
            "user_id": current_user["id"],
            "correct_answers": correct_answers,
            "total_quizzes": total_quizzes,
            "score_percentage": round((correct_answers / total_quizzes * 100) if total_quizzes > 0 else 0, 2)
        }
        
    except Exception as e:
        logger.error(f"Session quiz progress retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get session quiz progress")

@router.get("/history/course/{course_id}")
async def get_course_quiz_history(
    course_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get quiz history for a specific course from centralized storage"""
    try:
        supabase = get_supabase()
        
        # Get quiz history for the specific course
        result = supabase.table('quiz_responses').select('*').eq('course_id', course_id).eq('user_id', current_user["id"]).order('page_index', asc=True).execute()
        
        # Process and enrich quiz data (same as main history endpoint)
        quiz_history = result.data if result.data else []
        processed_quiz_history = _enrich_quiz_data(quiz_history)
        
        # Calculate course performance
        total_quizzes = len(processed_quiz_history)
        correct_answers = sum(1 for quiz in processed_quiz_history if quiz.get('correct', False))
        score = (correct_answers / total_quizzes * 100) if total_quizzes > 0 else 0
        
        return {
            "course_id": course_id,
            "user_id": current_user["id"],
            "quiz_history": processed_quiz_history,
            "total_quizzes": total_quizzes,
            "correct_answers": correct_answers,
            "score": round(score, 2)
        }
        
    except Exception as e:
        logger.error(f"Course quiz history retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get course quiz history")

@router.post("/session/")
async def create_new_session(current_user: dict = Depends(get_current_active_user)):
    """Create a new user session and return session data"""
    session_id = str(uuid.uuid4())
    session = await create_session(
        session_id=session_id, 
        user_id=current_user["id"]
    )
    return session