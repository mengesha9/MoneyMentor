import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from app.core.config import settings
from app.models.schemas import AIGeneratedCourse
import json

logger = logging.getLogger(__name__)

class AICourseService:
    """Service for generating personalized courses using OpenAI API"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL_GPT4_MINI,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.7
        )
        
        # Course type mappings
        self.course_type_mapping = {
            'money-goals-mindset': 'Money, Goals and Mindset',
            'budgeting-saving': 'Budgeting and Saving',
            'college-planning-saving': 'College Planning and Saving',
            'earning-income-basics': 'Earning and Income Basics'
        }
    
    async def generate_course(
        self,
        selected_course_type: str,
        quiz_responses: List[Dict[str, Any]],
        overall_score: float,
        user_id: str
    ) -> AIGeneratedCourse:
        """
        Generate a personalized 10-page course using OpenAI API
        
        Args:
            selected_course_type: The course type selected by the user
            quiz_responses: List of quiz responses with topics and correctness
            overall_score: User's overall quiz score (0-100)
            user_id: User's ID for personalization
            
        Returns:
            AIGeneratedCourse with title and 10 pages of content
        """
        try:
            # Determine course level based on score
            if overall_score >= 80:
                course_level = "Advanced"
            elif overall_score >= 60:
                course_level = "Intermediate"
            else:
                course_level = "Beginner"
            
            # Get human-readable course type
            focus_topic = self.course_type_mapping.get(selected_course_type, selected_course_type)
            
            # Analyze topic performance for personalization
            topic_analysis = self._analyze_topic_performance(quiz_responses)
            
            # Create the prompt for course generation
            prompt = self._create_course_generation_prompt(
                focus_topic=focus_topic,
                course_level=course_level,
                overall_score=overall_score,
                topic_analysis=topic_analysis
            )
            
            logger.info(f"Generating AI course for {focus_topic} at {course_level} level")
            
            # Generate course using OpenAI
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Parse the response
            try:
                course_data = json.loads(response.content)
                logger.info("Successfully parsed AI-generated course data")
                
                # Validate and create the course
                course = AIGeneratedCourse(
                    title=course_data.get('title', f"{course_level} {focus_topic}"),
                    pages=course_data.get('pages', [])
                )
                
                # Validate page count and content length
                if len(course.pages) < 5:
                    logger.warning(f"Course has very few pages: {len(course.pages)}. Expected at least 5 pages.")
                elif len(course.pages) != 10:
                    logger.info(f"Generated {len(course.pages)} pages (expected 10, but this is acceptable)")
                
                for i, page in enumerate(course.pages):
                    if len(page.get('content', '')) > 500:
                        logger.warning(f"Page {i+1} content exceeds 500 characters: {len(page.get('content', ''))}")
                
                logger.info(f"Successfully generated course: {course.title}")
                return course
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                logger.error(f"Raw response: {response.content}")
                raise ValueError("AI response was not valid JSON")
                
        except Exception as e:
            logger.error(f"Failed to generate AI course: {e}")
            raise
    
    def _analyze_topic_performance(self, quiz_responses: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze quiz performance by topic"""
        topic_analysis = {}
        
        for response in quiz_responses:
            topic = response.get('topic', 'Unknown')
            if topic not in topic_analysis:
                topic_analysis[topic] = {'total': 0, 'correct': 0, 'incorrect': 0}
            
            topic_analysis[topic]['total'] += 1
            if response.get('correct', False):
                topic_analysis[topic]['correct'] += 1
            else:
                topic_analysis[topic]['incorrect'] += 1
        
        # Calculate percentages
        for topic, stats in topic_analysis.items():
            if stats['total'] > 0:
                stats['percentage'] = (stats['correct'] / stats['total']) * 100
                stats['strength'] = 'strong' if stats['percentage'] >= 70 else 'weak' if stats['percentage'] <= 40 else 'moderate'
        
        return topic_analysis
    
    def _create_course_generation_prompt(
        self,
        focus_topic: str,
        course_level: str,
        overall_score: float,
        topic_analysis: Dict[str, Dict[str, Any]]
    ) -> str:
        """Create the prompt for course generation"""
        
        # Build topic analysis summary
        topic_summary = []
        for topic, stats in topic_analysis.items():
            topic_summary.append(f"- {topic}: {stats['correct']}/{stats['total']} correct ({stats['percentage']:.1f}%) - {stats['strength']}")
        
        topic_summary_text = "\n".join(topic_summary) if topic_summary else "No specific topic breakdown available"
        
        prompt = f"""You are an expert financial educator creating personalized courses for teenage students (middle school, high school, and early college). 

Generate a 10-page course on "{focus_topic}" at the {course_level} level, based on the following diagnostic results:

**Student Performance:**
- Overall Score: {overall_score}%
- Course Level: {course_level}
- Focus Topic: {focus_topic}

**Topic Performance Breakdown:**
{topic_summary_text}

**CRITICAL REQUIREMENTS FOR TEENAGE STUDENTS:**

**🎯 Age-Appropriate Content Guidelines:**
- Target audience: Teenage students (13-19 years old)
- Use relatable examples: saving for college, first car, phone, gaming console, etc.
- AVOID retirement-focused content (too far in the future for teens)
- Focus on immediate and near-term financial goals (next 1-5 years)
- Use language and examples that resonate with teen experiences

**📚 Course-Specific Requirements:**

**For "Money, Goals & Mindset":**
- Define what financial goals are and why they matter for teens
- Explain short-term vs. long-term goals with teen examples
- Cover money mindsets: spending vs. saving, instant vs. delayed gratification
- Examples: saving for college, first car, phone, gaming setup, summer trip
- Teach goal-setting techniques that work for teens

**For "Budgeting & Saving":**
- Explain what budgeting is and why teens need it
- Cover the 50/30/20 rule and other budgeting methods
- Define and explain emergency funds (why teens need them)
- Show how to create a simple budget for allowance, part-time job income
- Include saving strategies: automatic transfers, saving apps, etc.

**For "Earning & Income Basics":**
- Understanding paychecks: gross vs. net pay (simplified)
- Hourly wages vs. salary basics
- First jobs and internships for teens
- Work-study programs and student income
- Side hustles: tutoring, babysitting, pet sitting, lawn care
- Smart money habits when you start earning
- AVOID complex tax topics (not relevant for most teens)

**For "College Planning & Saving":**
- How to compare college costs (tuition, room & board, books)
- Basics of scholarships and grants (what they are, how to find them)
- High-level overview of student loans (what they are, when to consider them)
- Budgeting for college life: books, meals, transportation, housing
- Saving strategies for college expenses
- AVOID 529 plans (more relevant for parents)

**📖 Course Structure:**
- Page 1: Introduction and overview (what you'll learn and why it matters for teens)
- Pages 2-8: Core concepts with teen-specific examples and practical applications
- Page 9: Summary and key takeaways
- Page 10: Action steps and next steps (immediate actions teens can take)

**✅ Content Requirements:**
1. Create 8-10 pages (aim for 10, but 8+ is acceptable)
2. Each page must have a title and content
3. Each page's content must be 500 characters or less
4. Use engaging, conversational tone appropriate for teens
5. Include real-world examples that teens can relate to
6. Focus on areas where the student needs improvement
7. Make content interactive and encouraging
8. Ensure alignment between assessment topics and course content
9. Use encouraging language and practical examples

**Response Format:**
Return a JSON object with this exact structure:
{{
    "title": "Course Title Here",
    "pages": [
        {{"title": "Page Title", "content": "Page content (max 500 chars)..."}},
        {{"title": "Page Title", "content": "Page content (max 500 chars)..."}},
        ... (8-10 pages)
    ]
}}

**🎯 Key Focus Areas:**
- Ensure content directly addresses the concepts tested in assessments
- Use age-appropriate examples and language
- Make content practical and immediately actionable
- Focus on teen-relevant financial situations
- Avoid complex adult financial topics
- Keep examples relatable to teen experiences

Generate the course now:"""

        return prompt 