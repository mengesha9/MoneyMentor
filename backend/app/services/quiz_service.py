from typing import List, Dict, Any, Optional
import uuid
import json
import random
from datetime import datetime
import logging
import asyncio

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage

from app.core.config import settings
from app.models.schemas import QuizQuestion, QuizType
from app.services.content_service import ContentService
from app.core.database import get_supabase
from app.services.webhook_service import WebhookService
from app.services.google_sheets_service import GoogleSheetsService

logger = logging.getLogger(__name__)

class QuizService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL_GPT4_MINI,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.7
        )
        self.content_service = ContentService()
        self.supabase = get_supabase()
        self.sheets_service = GoogleSheetsService()
        self.webhook_service = WebhookService()
        self.quiz_frequency = settings.QUIZ_FREQUENCY
        
        # Predefined topics for diagnostic quiz - Age-appropriate for teenage students
        self.diagnostic_topics = [
            "Money Goals and Mindset",
            "Budgeting Basics",
            "Saving Strategies",
            "Emergency Funds",
            "Understanding Income",
            "First Jobs and Earning",
            "College Planning",
            "Scholarships and Grants",
            "Student Loans Basics",
            "Smart Spending Habits"
        ]
    
    def _parse_llm_json_response(self, response_content: str) -> Any:
        """
        Robust JSON parsing that handles both clean JSON and markdown-wrapped JSON responses.
        
        Args:
            response_content: Raw response content from LLM
            
        Returns:
            Parsed JSON data
            
        Raises:
            ValueError: If JSON cannot be parsed after all attempts
        """
        import re
        
        content = response_content.strip()
        
        # First, try to extract JSON from markdown code blocks
        markdown_patterns = [
            r'```json\s*\n(.*?)\n```',  # ```json ... ```
            r'```\s*\n(.*?)\n```',      # ``` ... ``` (generic code block)
            r'`([^`]+)`',                # `...` (inline code)
        ]
        
        for pattern in markdown_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                content = match.group(1).strip()
                break
        
        # Clean up common JSON issues
        try:
            # Remove trailing commas before closing braces and brackets
            content = re.sub(r',(\s*[}\]])', r'\1', content)
            
            # Try to parse the cleaned JSON
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            logger.warning(f"First JSON parse attempt failed: {e}")
            
            # Try more aggressive cleaning
            try:
                # Remove all trailing commas
                content = re.sub(r',(\s*[}\]])', r'\1', content)
                content = re.sub(r',(\s*})', r'\1', content)
                content = re.sub(r',(\s*\])', r'\1', content)
                
                # Remove any remaining markdown artifacts
                content = re.sub(r'^```.*?\n', '', content, flags=re.MULTILINE)
                content = re.sub(r'\n```.*?$', '', content, flags=re.MULTILINE)
                
                return json.loads(content)
                
            except json.JSONDecodeError as e2:
                logger.error(f"Failed to parse LLM response as JSON after cleaning: {e2}")
                logger.error(f"Original response: {response_content}")
                logger.error(f"Cleaned content: {content}")
                raise ValueError("LLM did not return valid JSON.")
    
    async def should_trigger_diagnostic(self, user_id: str) -> bool:
        """Check if diagnostic pre-test should be triggered"""
        try:
            # Check if user has completed diagnostic
            result = await asyncio.to_thread(
                lambda: self.supabase.table('quiz_attempts').select('*').eq('user_id', user_id).eq('quiz_type', 'diagnostic').execute()
            )
            return len(result.data) == 0
        except Exception as e:
            logger.error(f"Failed to check diagnostic status: {e}")
            return True
    
    async def generate_diagnostic_quiz(self, topic: str = None, difficulty: str = "mixed") -> List[Dict[str, Any]]:
        """Generate diagnostic pre-test questions focused on a specific topic"""
        try:
            if topic:
                if difficulty == "mixed":
                    # Generate 10 questions with mixed difficulties in a single call: 40% easy, 40% medium, 20% hard
                    prompt = (
                        f"Generate 10 multiple-choice questions for a diagnostic quiz focused on the topic: {topic}. "
                        f"All questions should be about {topic} and cover different aspects of this topic. "
                        f"Create a MIXED difficulty distribution: 4 EASY questions (40%), 4 MEDIUM questions (40%), and 2 HARD questions (20%). "
                        f"Return ONLY a valid JSON array of questions, no explanation, no markdown, no extra text. "
                        f"Each question should have: "
                        f"'question' (text), 'choices' (object with keys 'a', 'b', 'c', 'd' and string values), "
                        f"'correct_answer' (one of 'a', 'b', 'c', 'd'), 'explanation' (short explanation for the correct answer), "
                        f"and 'difficulty' (set to 'easy', 'medium', or 'hard' based on the question's complexity). "
                        f"Make sure to include exactly 4 easy, 4 medium, and 2 hard questions. "
                        f"IMPORTANT: Target teenage students (13-19 years old). Use age-appropriate examples and language. "
                        f"Focus on teen-relevant financial situations like saving for college, first car, phone, etc. "
                        f"AVOID complex adult topics like retirement planning, tax deductions, or 529 plans."
                    )
                else:
                    # Generate 10 questions with specific difficulty
                    prompt = (
                        f"Generate 10 multiple-choice questions for a diagnostic quiz focused on the topic: {topic}. "
                        f"All questions should be about {topic} and cover different aspects of this topic. "
                        f"The difficulty level should be {difficulty}. "
                        f"Return ONLY a valid JSON array of questions, no explanation, no markdown, no extra text. "
                        f"Each question should have: "
                        f"'question' (text), 'choices' (object with keys 'a', 'b', 'c', 'd' and string values), "
                        f"'correct_answer' (one of 'a', 'b', 'c', 'd'), 'explanation' (short explanation for the correct answer), "
                        f"and 'difficulty' (one of 'easy', 'medium', 'hard'). "
                        f"IMPORTANT: Target teenage students (13-19 years old). Use age-appropriate examples and language. "
                        f"Focus on teen-relevant financial situations like saving for college, first car, phone, etc. "
                        f"AVOID complex adult topics like retirement planning, tax deductions, or 529 plans."
                    )
            else:
                # Fallback to predefined topics if no specific topic provided
                topics = self.diagnostic_topics
                if difficulty == "mixed":
                    # Generate 10 questions with mixed difficulties for predefined topics
                    prompt = (
                        f"Generate 10 multiple-choice questions for a diagnostic quiz. "
                        f"Each question should cover one of these topics: {', '.join(topics)}. "
                        f"Create a MIXED difficulty distribution: 4 EASY questions (40%), 4 MEDIUM questions (40%), and 2 HARD questions (20%). "
                        f"Return ONLY a valid JSON array of questions, no explanation, no markdown, no extra text. "
                        f"Each question should have: "
                        f"'question' (text), 'choices' (object with keys 'a', 'b', 'c', 'd' and string values), "
                        f"'correct_answer' (one of 'a', 'b', 'c', 'd'), 'explanation' (short explanation for the correct answer), "
                        f"and 'difficulty' (set to 'easy', 'medium', or 'hard' based on the question's complexity). "
                        f"Make sure to include exactly 4 easy, 4 medium, and 2 hard questions. "
                        f"IMPORTANT: Target teenage students (13-19 years old). Use age-appropriate examples and language. "
                        f"Focus on teen-relevant financial situations like saving for college, first car, phone, etc. "
                        f"AVOID complex adult topics like retirement planning, tax deductions, or 529 plans."
                    )
                else:
                    # Generate 10 questions with specific difficulty
                    prompt = (
                        f"Generate 10 multiple-choice questions for a diagnostic quiz. "
                        f"Each question should cover one of these topics: {', '.join(topics)}. "
                        f"The difficulty level should be {difficulty}. "
                        f"Return ONLY a valid JSON array of questions, no explanation, no markdown, no extra text. "
                        f"Each question should have: "
                        f"'question' (text), 'choices' (object with keys 'a', 'b', 'c', 'd' and string values), "
                        f"'correct_answer' (one of 'a', 'b', 'c', 'd'), 'explanation' (short explanation for the correct answer), "
                        f"and 'difficulty' (one of 'easy', 'medium', 'hard'). "
                        f"IMPORTANT: Target teenage students (13-19 years old). Use age-appropriate examples and language. "
                        f"Focus on teen-relevant financial situations like saving for college, first car, phone, etc. "
                        f"AVOID complex adult topics like retirement planning, tax deductions, or 529 plans."
                    )
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Use the robust JSON parsing method
            questions = self._parse_llm_json_response(response.content)
            
            # Process all questions
            processed_questions = []
            for i, q in enumerate(questions):
                # Use the provided topic or assign from predefined list
                question_topic = topic if topic else self.diagnostic_topics[i % len(self.diagnostic_topics)]
                processed_questions.append({
                    'question': q.get('question', ''),
                    'choices': q.get('choices', {}),
                    'correct_answer': q.get('correct_answer', ''),
                    'explanation': q.get('explanation', ''),
                    'topic': question_topic,  # Add topic to each question
                    'difficulty': q.get('difficulty', difficulty)  # Add difficulty to each question
                })
            return processed_questions
        except Exception as e:
            logger.error(f"Failed to generate diagnostic quiz: {e}")
            return []
    
    async def _generate_question(self, topic: str) -> Optional[Dict[str, Any]]:
        """Generate a single quiz question for a specific topic using LLM"""
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
            
            # Use the robust JSON parsing method
            question_data = self._parse_llm_json_response(response.content)
            
            if 'question' in question_data and 'choices' in question_data and 'correct_answer' in question_data:
                    return {
                        'question': question_data['question'],
                        'choices': question_data['choices'],
                        'correct_answer': question_data['correct_answer'],
                        'explanation': question_data.get('explanation', '')
                    }
            return None
        except Exception as e:
            logger.error(f"Failed to generate question for topic {topic}: {e}")
            return None

    async def generate_micro_quiz(self, user_id: str, topic: str) -> Dict[str, Any]:
        """Generate a micro-quiz (3-5 questions) on a specific topic"""
        try:
            # Generate 3-5 questions on the topic
            questions = []
            num_questions = min(5, max(3, len(topic.split())))  # 3-5 questions based on topic complexity
            
            for _ in range(num_questions):
                question = await self._generate_question(topic)
                questions.append(question)
            
            quiz_id = str(uuid.uuid4())
            quiz_data = {
                "quiz_id": quiz_id,
                "user_id": user_id,
                "type": "micro",
                "topic": topic,
                "questions": questions,
                "created_at": datetime.utcnow().isoformat(),
                "status": "pending"
            }
            
            # Store quiz in Supabase
            result = await asyncio.to_thread(
                lambda: self.supabase.table('quizzes').insert(quiz_data).execute()
            )
            
            return quiz_data
            
        except Exception as e:
            logger.error(f"Failed to generate micro quiz: {e}")
            raise

    async def log_quiz_response(self, quiz_id: str, responses: List[Dict[str, Any]]) -> bool:
        """Log quiz responses and update progress"""
        try:
            # Get quiz data
            quiz = await asyncio.to_thread(
                lambda: self.supabase.table('quizzes').select('*').eq('quiz_id', quiz_id).execute()
            )
            if not quiz.data:
                raise ValueError(f"Quiz {quiz_id} not found")
            
            quiz_data = quiz.data[0]
            
            # Calculate score and analyze responses
            score = self._calculate_score(quiz_data['questions'], responses)
            analysis = self._analyze_responses(quiz_data['questions'], responses)
            
            # Update quiz with responses
            update_data = {
                "responses": responses,
                "score": score,
                "analysis": analysis,
                "completed_at": datetime.utcnow().isoformat(),
                "status": "completed"
            }
            
            result = await asyncio.to_thread(
                lambda: self.supabase.table('quizzes').update(update_data).eq('quiz_id', quiz_id).execute()
            )
            
            # Update user progress
            await self._update_user_progress(quiz_data['user_id'], quiz_data['type'], score, analysis)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log quiz responses: {e}")
            return False

    async def _get_topics(self) -> List[str]:
        """Get comprehensive list of topics from content"""
        try:
            # Query Supabase for content topics
            result = await asyncio.to_thread(
                lambda: self.supabase.table('content_topics').select('topic').execute()
            )
            return [row['topic'] for row in result.data]
        except Exception as e:
            logger.error(f"Failed to get topics: {e}")
            return []

    async def log_quiz_attempt(
        self,
        user_id: str,
        quiz_id: str,
        selected_option: int,
        correct: bool,
        topic: str,
        quiz_type: str = "micro",
        session_id: str = None
    ) -> bool:
        """Log a quiz attempt"""
        try:
            # Store in database
            attempt_data = {
                "user_id": user_id,
                "quiz_id": quiz_id,
                "selected_option": selected_option,
                "correct": correct,
                "topic": topic,
                "quiz_type": quiz_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await asyncio.to_thread(
                lambda: self.supabase.table('quiz_attempts').insert(attempt_data).execute()
            )
            
            # Log to Google Sheets
            try:
                # Convert selected_option number to letter (0->A, 1->B, 2->C, 3->D)
                option_letters = ['A', 'B', 'C', 'D']
                selected_letter = option_letters[selected_option] if 0 <= selected_option < 4 else str(selected_option)
                
                quiz_log_data = {
                    "user_id": user_id,
                    "quiz_id": quiz_id,
                    "topic_tag": topic,
                    "selected_option": selected_letter,
                    "correct": correct,
                    "session_id": session_id or user_id  # Use session_id if provided, otherwise fallback to user_id
                }
                self.sheets_service.log_quiz_response(quiz_log_data)
                
            except Exception as e:
                logger.warning(f"Failed to log quiz response to Google Sheets: {e}")
                # Don't fail the main request if logging fails
            
            # Update course statistics in database only - let background service handle Google Sheets sync
            try:
                from app.services.course_statistics_service import CourseStatisticsService
                stats_service = CourseStatisticsService()
                
                # Update user's course statistics in database
                await stats_service.update_user_profile_statistics(user_id)
                logger.info(f"Updated course statistics in database for user {user_id}")
                
                # Note: Google Sheets sync is handled by background service to avoid multiple update sources
                
            except Exception as e:
                logger.warning(f"Failed to update course statistics: {e}")
            
            # Send to webhook
            await self.webhook_service.log_quiz_attempt(attempt_data)
            
            return True
        except Exception as e:
            logger.error(f"Failed to log quiz attempt: {e}")
            return False
    
    async def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """Get user's quiz progress"""
        try:
            # Get all quiz attempts
            result = await asyncio.to_thread(
                lambda: self.supabase.table('quiz_attempts').select('*').eq('user_id', user_id).execute()
            )
            
            # Calculate statistics
            total_attempts = len(result.data)
            correct_attempts = sum(1 for attempt in result.data if attempt['correct'])
            
            # Group by topic
            topic_stats = {}
            for attempt in result.data:
                topic = attempt['topic']
                if topic not in topic_stats:
                    topic_stats[topic] = {'total': 0, 'correct': 0}
                topic_stats[topic]['total'] += 1
                if attempt['correct']:
                    topic_stats[topic]['correct'] += 1
            
            return {
                'total_attempts': total_attempts,
                'correct_attempts': correct_attempts,
                'accuracy': correct_attempts / total_attempts if total_attempts > 0 else 0,
                'topic_stats': topic_stats
            }
        except Exception as e:
            logger.error(f"Failed to get user progress: {e}")
            return {}

    def _calculate_score(self, questions: List[Dict[str, Any]], responses: List[Dict[str, Any]]) -> float:
        """Calculate quiz score"""
        try:
            correct = 0
            for q, r in zip(questions, responses):
                if q['correct_answer'] == r['answer']:
                    correct += 1
            return (correct / len(questions)) * 100
        except Exception as e:
            logger.error(f"Failed to calculate score: {e}")
            return 0.0

    def _analyze_responses(self, questions: List[Dict[str, Any]], responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze quiz responses for insights"""
        try:
            analysis = {
                "strengths": [],
                "weaknesses": [],
                "recommendations": []
            }
            
            # Analyze each response
            for q, r in zip(questions, responses):
                if q['correct_answer'] == r['answer']:
                    analysis['strengths'].append(q['topic'])
                else:
                    analysis['weaknesses'].append(q['topic'])
            
            # Generate recommendations based on weaknesses
            for weakness in analysis['weaknesses']:
                analysis['recommendations'].append(f"Review {weakness} concepts")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze responses: {e}")
            return {"error": str(e)}

    async def _update_user_progress(self, user_id: str, quiz_type: str, score: float, 
                                  analysis: Dict[str, Any]) -> bool:
        """Update user progress based on quiz results"""
        try:
            # Get current progress
            result = await asyncio.to_thread(
                lambda: self.supabase.table('user_progress').select('*').eq('user_id', user_id).execute()
            )
            current_progress = result.data[0] if result.data else {}
            
            # Update progress
            progress_data = {
                'user_id': user_id,
                'last_quiz_type': quiz_type,
                'last_quiz_score': score,
                'last_quiz_date': datetime.utcnow().isoformat(),
                'strengths': analysis.get('strengths', []),
                'weaknesses': analysis.get('weaknesses', []),
                'recommendations': analysis.get('recommendations', [])
            }
            
            # Store in Supabase
            await asyncio.to_thread(
                lambda: self.supabase.table('user_progress').upsert(progress_data).execute()
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user progress: {e}")
            return False
    
    def validate_answer(self, question_id: str, selected_option: int, correct_answer: int) -> Dict[str, Any]:
        """Validate a quiz answer and return result"""
        is_correct = selected_option == correct_answer
        
        return {
            "correct": is_correct,
            "selected_option": selected_option,
            "correct_answer": correct_answer
        }
    
    def get_quiz_explanation(self, question_data: Dict[str, Any], selected_option: int) -> str:
        """Get explanation for quiz answer"""
        explanation = question_data.get("explanation", "")
        
        if selected_option == question_data.get("correct_answer"):
            return f"✅ Correct! {explanation}"
        else:
            correct_option = question_data.get("options", [])[question_data.get("correct_answer", 0)]
            return f"❌ Incorrect. The correct answer is: {correct_option}. {explanation}"
    
    def should_trigger_quiz(self, user_id: str, chat_count: int) -> bool:
        """Determine if a micro-quiz should be triggered"""
        # Trigger quiz every N chat interactions
        return chat_count > 0 and chat_count % settings.QUIZ_TRIGGER_INTERVAL == 0
    
    def extract_topic_from_message(self, message: str) -> str:
        """Extract the main topic from a user message for micro-quiz generation"""
        try:
            prompt = PromptTemplate(
                input_variables=["message"],
                template="""
                Analyze this user message and identify the main financial topic being discussed:
                "{message}"
                
                Return only the topic name (e.g., "Investing", "Debt Management", "Savings", "Retirement Planning", etc.)
                If no clear financial topic is identified, return "General Finance".
                """
            )
            
            formatted_prompt = prompt.format(message=message)
            response = self.llm.invoke([HumanMessage(content=formatted_prompt)])
            
            topic = response.content.strip().replace('"', '')
            return topic if topic else "General Finance"
            
        except Exception as e:
            logger.error(f"Error extracting topic from message: {e}")
            return "General Finance"

    async def generate_quiz_from_history(self, session_id: str, quiz_type: str, difficulty: str, chat_history: list) -> list:
        """Generate a quiz based on chat history, quiz_type, and difficulty. Deduces topic from chat history."""
        try:
            # Extract topic from the most recent user message
            user_messages = [msg["content"] for msg in chat_history if msg.get("role") == "user"]
            last_user_message = user_messages[-1] if user_messages else ""
            topic = self.extract_topic_from_message(last_user_message)

            # Prepare prompt for LLM
            chat_context = "\n".join([
                f"{msg['role']}: {msg['content']}" for msg in chat_history if 'role' in msg and 'content' in msg
            ])
            prompt = (
                f"You are a financial education assistant. Based on the following chat history, "
                f"generate a {quiz_type} quiz for the user. The quiz should be about the specific topic: {topic}. "
                f"The difficulty should be {difficulty}.\n"
                f"Chat history:\n{chat_context}\n"
                f"Return a JSON array of questions. Each question should have: 'question' (text), 'choices' (an object with keys 'a', 'b', 'c', 'd' and string values), 'correct_answer' (one of 'a', 'b', 'c', 'd'), 'explanation' (short explanation for the correct answer), and 'difficulty' (one of 'easy', 'medium', 'hard'). Example format: [{{'question': '...', 'choices': {{'a': '...', 'b': '...', 'c': '...', 'd': '...'}}, 'correct_answer': 'a', 'explanation': '...', 'difficulty': 'medium'}}]"
            )
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Use the robust JSON parsing method
            questions = self._parse_llm_json_response(response.content)

            # Post-process to ensure structure and add topic information only for diagnostic quizzes
            processed_questions = []
            for q in questions:
                # If 'options' is present, convert to 'choices'
                if 'options' in q and isinstance(q['options'], list) and len(q['options']) == 4:
                    q['choices'] = {k: v for k, v in zip(['a', 'b', 'c', 'd'], q['options'])}
                    q.pop('options')
                # If 'choices' is present but not a dict, try to fix
                if 'choices' in q and not isinstance(q['choices'], dict):
                    if isinstance(q['choices'], list) and len(q['choices']) == 4:
                        q['choices'] = {k: v for k, v in zip(['a', 'b', 'c', 'd'], q['choices'])}
                
                # Base question structure
                question_data = {
                    'question': q.get('question', ''),
                    'choices': q.get('choices', {}),
                    'correct_answer': q.get('correct_answer', ''),
                    'explanation': q.get('explanation', ''),
                    'difficulty': q.get('difficulty', difficulty)  # Add difficulty to each question
                }
                
                # Only add topic for diagnostic quizzes
                if quiz_type == "diagnostic":
                    question_data['topic'] = topic
                
                processed_questions.append(question_data)
            return processed_questions
        except Exception as e:
            logger.error(f"Failed to generate quiz from history: {e}")
            raise 

    def _get_course_name_from_topic(self, topic: str) -> str:
        """
        Map topic to course name
        
        Args:
            topic: The topic string from quiz
            
        Returns:
            Course name or None if no mapping found
        """
        # Topic to course mapping
        topic_to_course = {
            # Budgeting and Saving topics
            "budgeting": "Budgeting and Saving",
            "saving": "Budgeting and Saving", 
            "expenses": "Budgeting and Saving",
            "income": "Budgeting and Saving",
            "budget": "Budgeting and Saving",
            
            # Money, Goals and Mindset topics
            "goals": "Money, Goals and Mindset",
            "mindset": "Money, Goals and Mindset",
            "financial_goals": "Money, Goals and Mindset",
            "money_mindset": "Money, Goals and Mindset",
            "goal_setting": "Money, Goals and Mindset",
            
            # Investing topics
            "investing": "Investing Basics",
            "stocks": "Investing Basics",
            "bonds": "Investing Basics",
            "portfolio": "Investing Basics",
            "investment": "Investing Basics",
            
            # Debt Management topics
            "debt": "Debt Management",
            "credit": "Debt Management",
            "loans": "Debt Management",
            "interest": "Debt Management",
            "credit_score": "Debt Management",
            
            # Emergency Fund topics
            "emergency_fund": "Emergency Fund",
            "emergency": "Emergency Fund",
            "savings": "Emergency Fund",
            "financial_safety": "Emergency Fund"
        }
        
        # Try exact match first
        if topic.lower() in topic_to_course:
            return topic_to_course[topic.lower()]
        
        # Try partial match
        topic_lower = topic.lower()
        for key, course in topic_to_course.items():
            if key in topic_lower or topic_lower in key:
                return course
        
        # Default mapping based on common patterns
        if any(word in topic_lower for word in ["budget", "save", "expense", "income"]):
            return "Budgeting and Saving"
        elif any(word in topic_lower for word in ["goal", "mindset", "financial"]):
            return "Money, Goals and Mindset"
        elif any(word in topic_lower for word in ["invest", "stock", "bond", "portfolio"]):
            return "Investing Basics"
        elif any(word in topic_lower for word in ["debt", "credit", "loan", "interest"]):
            return "Debt Management"
        elif any(word in topic_lower for word in ["emergency", "safety"]):
            return "Emergency Fund"
        
        # If no match found, return None
        return None 