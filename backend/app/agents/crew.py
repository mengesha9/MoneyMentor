from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from typing import Dict, Any, List
import logging
import time
from fastapi import HTTPException
import re

from app.core.config import settings
from app.agents.tools import (
    QuizGeneratorTool,
    QuizLoggerTool,
    FinancialCalculatorTool,
    ContentRetrievalTool,
    SessionManagerTool,
    ProgressTrackerTool
)
from app.services.content_service import ContentService

logger = logging.getLogger(__name__)

class MoneyMentorCrew:
    def __init__(self):
        self.llm_gpt4 = ChatOpenAI(
            model_name=settings.OPENAI_MODEL_GPT4,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.1,
            request_timeout=30,
            max_retries=2,
            streaming=True,
            provider="openai"
        )
        
        self.llm_gpt4_mini = ChatOpenAI(
            model_name=settings.OPENAI_MODEL_GPT4_MINI,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.0,  # Set to 0 for maximum speed and determinism
            request_timeout=30,  # Increased timeout for reliability
            max_retries=2,  # Allow retries for reliability
            streaming=True,
            provider="openai",
            # PERFORMANCE OPTIMIZATIONS
            max_tokens=1024,  # Increased for complete responses
            presence_penalty=0.0,  # Disable presence penalty for faster responses
            frequency_penalty=0.0,  # Disable frequency penalty for faster responses
            # Optimize for function calling
            function_call="auto",  # Enable automatic function calling
        )
        
        # Initialize tools - ONLY for chat/message endpoint
        self.tools = [
            FinancialCalculatorTool(),
            # ContentRetrievalTool removed - using pre-retrieved context instead for better performance
            # Commented out tools not used in chat/message endpoint
            # QuizGeneratorTool(),
            # QuizLoggerTool(),
            # SessionManagerTool(),
            # ProgressTrackerTool()
        ]
        
        # Create agents - ONLY the one used for chat/message endpoint
        self.financial_tutor_agent = self._create_financial_tutor_agent()
        
        # Commented out agents not used in chat/message endpoint
        # self.quiz_master_agent = self._create_quiz_master_agent()
        # self.calculation_agent = self._create_calculation_agent()
        # self.progress_tracker_agent = self._create_progress_tracker_agent()
        
    def _get_calculation_description(self, calculation_type: str) -> str:
        """Get human-readable description of calculation type"""
        descriptions = {
            'credit_card_payoff': 'debt payoff timeline',
            'savings_goal': 'savings goal projection',
            'student_loan': 'student loan amortization'
        }
        return descriptions.get(calculation_type, calculation_type)

    def _determine_calculation_type(self, message: str) -> str:
        """Determine calculation type based on message content"""
        message_lower = message.lower()
        
        # Check for savings goal indicators
        if any(word in message_lower for word in ['save', 'savings', 'goal', 'college', 'tuition', 'need', 'want']):
            return 'savings_goal'
        # Check for student loan indicators
        elif any(word in message_lower for word in ['student', 'loan', 'borrow', 'principal']):
            return 'student_loan'
        # Default to credit card payoff for debt-related questions
        else:
            return 'credit_card_payoff'
    
    def _map_parameters_for_calculation_type(self, params: Dict[str, Any], calculation_type: str) -> Dict[str, Any]:
        """Map extracted parameters to the correct parameter names for each calculation type"""
        if calculation_type == 'savings_goal':
            # Map balance -> target_amount, apr -> interest_rate
            # Use default interest rate of 5% for savings if not provided
            interest_rate = params.get('apr', 5.0)  # Default to 5% for savings
            return {
                'target_amount': params.get('balance', 0),
                'interest_rate': interest_rate,
                'target_months': params.get('target_months', 0)
            }
        elif calculation_type == 'student_loan':
            # Map balance -> principal, apr -> interest_rate
            return {
                'principal': params.get('balance', 0),
                'interest_rate': params.get('apr', 0),
                'term_months': params.get('target_months', 0)
            }
        else:  # credit_card_payoff
            # Keep original parameter names
            return params

    def _extract_calculation_params(self, message: str) -> Dict[str, Any]:
        """Extract calculation parameters using regex - only real extracted data, no defaults"""
        import re
        params = {}
        
        # Extract dollar amounts with better pattern matching
        dollar_patterns = [
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',  # $6,000.00
            r'\$(\d+)\s*k',  # $6k
            r'\$(\d+)\s*thousand',  # $6 thousand
            r'(\d+)\s*k\s+dollars?',  # 6k dollars
            r'(\d+)\s+thousand\s+dollars?',  # 6 thousand dollars
        ]
        
        for pattern in dollar_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                amount_str = matches[0].replace(',', '')
                amount = float(amount_str)
                
                # Convert k/thousand to actual amount
                if 'k' in pattern or 'thousand' in pattern:
                    amount *= 1000
                
                # Determine parameter name based on context
                message_lower = message.lower()
                if any(word in message_lower for word in ['save', 'goal', 'need', 'want', 'target']):
                    params['target_amount'] = amount
                else:
                    params['balance'] = amount
                break
        
        # Extract percentages with better pattern matching
        percent_patterns = [
            r'(\d+(?:\.\d+)?)\s*%',  # 22% or 22.5%
            r'(\d+(?:\.\d+)?)\s*percent',  # 22 percent
            r'apr\s+of\s+(\d+(?:\.\d+)?)',  # APR of 22
            r'interest\s+rate\s+of\s+(\d+(?:\.\d+)?)',  # interest rate of 22
        ]
        
        for pattern in percent_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                params['apr'] = float(matches[0])
                break
        
        # Extract time periods with better pattern matching
        time_patterns = [
            (r'(\d+)\s*months?', 'target_months'),  # 12 months
            (r'(\d+)\s*mo', 'target_months'),  # 12 mo
            (r'(\d+)\s*years?', 'target_months'),  # 3 years -> 36 months
            (r'(\d+)\s*yr', 'target_months'),  # 3 yr -> 36 months
        ]
        
        for pattern, param_name in time_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                value = int(matches[0])
                if 'year' in pattern or 'yr' in pattern:
                    value *= 12  # Convert years to months
                params[param_name] = value
                break
        
        # Extract monthly payment if specified
        payment_patterns = [
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s+(?:per\s+)?month',  # $500 per month
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s+dollars?\s+(?:per\s+)?month',  # 500 dollars per month
            r'monthly\s+payment\s+of\s+\$(\d+(?:,\d{3})*(?:\.\d{2})?)',  # monthly payment of $500
        ]
        
        for pattern in payment_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                amount_str = matches[0].replace(',', '')
                params['monthly_payment'] = float(amount_str)
                break
        
        return params

    def _format_chat_history(self, chat_history: List[Dict[str, str]], is_calculation: bool = False) -> str:
        """Format chat history into a readable string, filtering calculation results for general chat"""
        if not chat_history:
            return "No previous messages."
            
        formatted_history = []
        for msg in chat_history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            
            # For general chat requests, filter out calculation results to prevent contamination
            if not is_calculation and role == "assistant":
                # Check if this is a calculation result
                if any(keyword in content.lower() for keyword in [
                    "calculation result", "monthly payment", "total interest", 
                    "step-by-step plan", "apr:", "balance:", "```json"
                ]):
                    # Replace calculation results with a simple acknowledgment
                    content = "I provided a financial calculation in response to your previous question."
            
            formatted_history.append(f"{role.upper()} ({timestamp}): {content}")
            
        return "\n".join(formatted_history)
        
    async def process_message(self, message: str, chat_history: List[Dict[str, str]], session_id: str, context: str = "") -> Dict[str, Any]:
        """Process a user message and generate a response with parallel optimization"""
        crew_start_time = time.time()
        print(f"            🚀 CrewAI.process_message() started")
        
        try:
            # Step 1: PARALLEL OPTIMIZATION - Run ALL operations simultaneously
            step1_start = time.time()
            print(f"               ⚡ Step 2.1: PARALLEL - Chat History + Calculation detection + Content retrieval...")
            
            # Create parallel tasks
            import asyncio
            
            # Task 1: Specific calculation detection (fast regex operation)
            async def detect_calculation():
                """Specific calculation detection using precise regex patterns"""
                import re
                
                # More specific calculation patterns that require actual numbers
                calculation_patterns = [
                    r'\$\d+(?:,\d{3})*(?:\.\d{2})?',  # Dollar amounts like $6,000.00
                    r'\d+(?:\.\d+)?\s*%',  # Percentage rates like 22% or 22.5%
                    r'how\s+much\s+(?:do\s+I\s+need\s+to\s+)?(?:pay|save|contribute)',  # "how much do I need to pay"
                    r'how\s+long\s+(?:will\s+it\s+take\s+to\s+)?(?:pay\s+off|clear|reach)',  # "how long will it take to pay off"
                    r'(?:pay\s+off|clear)\s+\$\d+',  # "pay off $6000"
                    r'\d+\s*(?:months?|years?)\s+(?:to\s+)?(?:pay\s+off|clear|reach)',  # "12 months to pay off"
                    r'monthly\s+payment\s+(?:of\s+)?\$\d+',  # "monthly payment of $500"
                    r'\$\d+\s+(?:per\s+)?month',  # "$500 per month"
                ]
                
                # Check for specific calculation patterns
                has_calculation_pattern = any(re.search(pattern, message.lower()) for pattern in calculation_patterns)
                
                # Check for definition/educational questions to exclude
                definition_patterns = [
                    r'^what\s+is\s+',  # "What is APR?"
                    r'^how\s+does\s+',  # "How does APR work?"
                    r'^explain\s+',  # "Explain APR"
                    r'^tell\s+me\s+about\s+',  # "Tell me about APR"
                    r'^define\s+',  # "Define APR"
                    r'^why\s+',  # "Why is APR important?"
                ]
                
                is_definition_question = any(re.search(pattern, message.lower()) for pattern in definition_patterns)
                
                # Check if the question contains financial keywords but no numbers
                financial_keywords = [
                    'apr', 'interest rate', 'balance', 'payment', 'loan', 'credit card',
                    'savings', 'goal', 'debt', 'principal', 'amortization', 'compound interest'
                ]
                
                has_financial_keywords = any(keyword in message.lower() for keyword in financial_keywords)
                
                # Check for numbers in the message
                has_numbers = bool(re.search(r'\d+', message))
                
                # If it's a definition question with financial keywords but no numbers, treat as regular chat
                if is_definition_question and has_financial_keywords and not has_numbers:
                    return False
                
                # Return True only if it has specific calculation patterns
                return has_calculation_pattern
            
            # Task 2: Content retrieval from vector database
            async def retrieve_content():
                """Retrieve relevant content from knowledge base"""
                try:
                    content_service = ContentService()
                    content_results = await content_service.search_content(
                        message, 
                        limit=2,  # Reduced from 3 to 2 for faster retrieval
                        threshold=0.2  # Reduced from 0.3 to 0.2 for more results
                    )
                    if content_results and isinstance(content_results, list):
                        # Format the content results into a readable context
                        context = "\n".join([
                            f"- {item.get('content', '')[:200]}"  # Limit content length to 200 chars
                            for item in content_results[:2]  # Limit to top 2 most relevant results
                        ])
                        logger.info(f"Retrieved context from knowledge base: {context[:100]}...")
                        return context
                    else:
                        logger.info("No relevant context found in knowledge base")
                        return ""
                except Exception as e:
                    logger.error(f"Failed to retrieve context from knowledge base: {e}")
                    return ""  # Reset to empty if retrieval fails
            
            # Task 3: Get chat history (if not provided)
            async def get_chat_history():
                """Get chat history from session if not provided"""
                if chat_history:
                    return chat_history
                try:
                    # Import here to avoid circular imports
                    from app.utils.session import get_session
                    session = await get_session(session_id)
                    if session:
                        return session.get("chat_history", [])
                    return []
                except Exception as e:
                    logger.error(f"Failed to get chat history: {e}")
                    return []
            
            # Execute ALL three tasks in parallel
            parallel_results = await asyncio.wait_for(
                asyncio.gather(
                    detect_calculation(),
                    retrieve_content(),
                    get_chat_history(),
                    return_exceptions=True
                ),
                timeout=5.0  # 5 second timeout for parallel operations
            )
            
            # Extract results
            is_calculation = parallel_results[0] if not isinstance(parallel_results[0], Exception) else False
            context = parallel_results[1] if not isinstance(parallel_results[1], Exception) else ""
            retrieved_chat_history = parallel_results[2] if not isinstance(parallel_results[2], Exception) else []
            
            # Use retrieved chat history if original was empty
            final_chat_history = chat_history if chat_history else retrieved_chat_history
            
            step1_time = time.time() - step1_start
            print(f"               ✅ Step 2.1 completed in {step1_time:.3f}s (PARALLEL - Chat History + Calc detection + Content retrieval)")
            print(f"                  - Calculation detected: {is_calculation}")
            print(f"                  - Context retrieved: {len(context)} chars")
            print(f"                  - Chat history retrieved: {len(final_chat_history)} messages")
            
            # Step 2: Crew creation with optimized task description
            step2_start = time.time()
            print(f"               🏗️ Step 2.2: Crew creation...")
            
            # Create optimized task description based on calculation detection
            if is_calculation:
                # Get pre-extracted parameters from chat service
                calc_params = self._extract_calculation_params(message)
                calculation_type = self._determine_calculation_type(message)
                
                # Check if we have enough parameters to perform a calculation
                if not calc_params:
                    # No parameters extracted - treat as regular chat and ask for more information
                    task_description = f"""The user asked a calculation question but didn't provide enough specific numbers: {message}

                    Since no calculation parameters were extracted, respond as a helpful financial advisor:
                    1. Acknowledge their question
                    2. Explain what information you need to perform the calculation
                    3. Ask for specific amounts, rates, and timeframes
                    4. Provide educational context about why this information is important

                    Example: "I'd be happy to help you with that calculation! To give you an accurate result, I'll need:
                    - The amount (e.g., $6,000)
                    - The interest rate (e.g., 22% APR)
                    - The timeframe (e.g., 12 months)
                    
                    Could you provide these details?"

                    Keep your response friendly and educational.
                    """
                else:
                    # We have parameters - perform the calculation
                    mapped_params = self._map_parameters_for_calculation_type(calc_params, calculation_type)
                    task_description = f"""You are a financial calculator. The user asked: {message}

                        You have access to the FinancialCalculatorTool. Use it with these parameters:
                        - calculation_type: "{calculation_type}"
                        - params: {mapped_params}

                        IMPORTANT: Follow this exact process:
                        1. Call the FinancialCalculatorTool to get the calculation results
                        2. Use the returned JSON data to explain the results in plain English
                        3. Do NOT show the raw JSON to the user
                        4. Explain the monthly payment, timeline, and total interest in simple terms
                        5. Use the step_by_step_plan to provide educational context
                        6. End with: "Estimates only. Verify with a certified financial professional."

                        Example response format:
                        "Based on your calculation, you would need to save $516.08 per month to reach your $20,000 goal in 3 years. This means you'll contribute a total of $18,579.05 and earn $1,420.95 in interest. 

                        Here's how it works:
                        - Starting with $0.00 in savings
                        - Target amount: $20,000.00
                        - Timeframe: 36 months
                        - Interest rate: 5.0% annually
                        - Monthly contribution needed: $516.08
                        - Total contributions: $18,579.05
                        - Interest earned: $1,420.95
                        - Final amount: $20,000.00

                        Estimates only. Verify with a certified financial professional."

                        Execute the tool call now and explain the results naturally.
                        """
            else:
                task_description = f"""You are a friendly financial education tutor. The user said: "{message}"

                Use the following context from our knowledge base if relevant:
                {context if context else "No specific content found in knowledge base - use your general financial education knowledge"}
                
                Previous chat history:
                {self._format_chat_history(final_chat_history, is_calculation)}
                
                IMPORTANT: This is a GENERAL CONVERSATION REQUEST, NOT a calculation.
                
                DO NOT use the FinancialCalculatorTool for this request.
                DO NOT mention calculations or financial tools.
                
                Provide a complete, helpful response that:
                1. Acknowledges the user's message
                2. Uses the provided context if relevant
                3. Offers helpful financial education information
                4. Maintains a friendly, conversational tone
                5. Is educational and informative
                
                Keep your responses natural and conversational while maintaining professionalism.
                Be friendly, helpful, and engaging in your response.
                Complete your response fully - do not cut off mid-sentence.
                """
            
            # Create a chat crew for this message
            chat_crew = Crew(
                agents=[self.financial_tutor_agent],
                tasks=[
                    Task(
                        description=task_description,
                        agent=self.financial_tutor_agent,
                        expected_output="Helpful response. For calculations: JSON + explanation + disclaimer."
                    )
                ],
                process=Process.sequential,
                verbose=False,  # Reduced logging overhead for faster responses
                # Additional Crew optimizations
                memory=False,  # Disable crew-level memory
                max_rpm=50,  # Increase RPM for faster processing
                # Optimize for single-task execution
                enable_planning=False,  # Disable planning for single task
                enable_reasoning=False,  # Disable reasoning for single task
                # Increase context usage for better responses
                max_context_length=2000,  # Increased for better context
                # Disable unnecessary features
                human_input=False,  # Disable human input requests
                # Optimize for speed
                temperature=0.0,  # Lower temperature for deterministic responses
                # Disable features that add overhead
                enable_search=False,  # Disable built-in search
                enable_code_execution=False,  # Disable code execution
                # Allow more iterations for complete responses
                max_iterations=2,  # Increased to 2 iterations for complete responses
                # Optimize for single response
                allow_delegation=False,  # Disable delegation for single agent
                # Increase token limit for complete responses
                max_tokens_per_task=1024,  # Increased token limit
                # Disable telemetry to prevent connection errors
                disable_telemetry=True,  # Disable CrewAI telemetry
            )
            
            step2_time = time.time() - step2_start
            print(f"               ✅ Step 2.2 completed in {step2_time:.3f}s (Crew creation)")
            
            # Step 3: Crew execution (MAIN BOTTLENECK)
            step3_start = time.time()
            print(f"               ⚡ Step 2.3: Crew execution (MAIN BOTTLENECK)...")
            
            try:
                # Process the message
                print(f"               🔄 Starting CrewAI kickoff...")
                result = await chat_crew.kickoff_async()
                print(f"               ✅ CrewAI kickoff completed")
                
                # Ensure result is a string
                if hasattr(result, 'raw_output'):
                    result = result.raw_output
                elif hasattr(result, 'output'):
                    result = result.output
                elif not isinstance(result, str):
                    result = str(result)
                
                print(f"               📝 Result type: {type(result)}")
                print(f"               📝 Result length: {len(str(result))}")
                
                # SIMPLIFIED: Only run post-processing for calculation requests
                def needs_step3_enforcement(msg):
                    """Only enforce if it's a calculation request AND no JSON block exists"""
                    return is_calculation and '```json' not in msg

                # SIMPLIFIED: Only run post-processing for calculation requests
                if needs_step3_enforcement(str(result)):
                    # For calculation requests, let CrewAI handle it naturally
                    # Only add a simple disclaimer if no JSON is present
                    if '```json' not in str(result):
                        result = f"{result}\n\nEstimates only. Verify with a certified financial professional."
                        logger.info("Added disclaimer to calculation response")
                
                step3_time = time.time() - step3_start
                print(f"               ✅ Step 2.3 completed in {step3_time:.3f}s (Crew execution)")
                
                # Initialize response dictionary
                response = {
                    "message": result,
                    "session_id": session_id,
                    "quiz": None,
                    "is_calculation": is_calculation  # Add calculation flag for debugging
                }
                
                # Total CrewAI timing
                crew_total_time = time.time() - crew_start_time
                print(f"            🏁 CrewAI completed in {crew_total_time:.3f}s")
                print(f"               📊 CrewAI Breakdown:")
                print(f"                  - PARALLEL (Chat History + Calc + Content): {step1_time:.3f}s ({(step1_time/crew_total_time)*100:.1f}%)")
                print(f"                  - Crew creation: {step2_time:.3f}s ({(step2_time/crew_total_time)*100:.1f}%)")
                print(f"                  - Crew execution: {step3_time:.3f}s ({(step3_time/crew_total_time)*100:.1f}%)")
                
                return response
                
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                logger.error(f"Crew execution failed: {str(e)}")
                logger.error(f"Error details: {error_details}")
                print(f"               ❌ Crew execution failed: {str(e)}")
                print(f"               📋 Error details: {error_details}")
                
                # Return a fallback response if crew fails
                return {
                    "message": "I apologize, but I'm having trouble processing your request right now. Please try again in a moment.",
                    "session_id": session_id,
                    "quiz": None,
                    "error": f"Crew execution failed: {str(e)}",
                    "error_details": error_details
                }
            
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process message: {str(e)}"
            )

    def _create_financial_tutor_agent(self) -> Agent:
        """Create the main financial education tutor agent - OPTIMIZED for chat/message endpoint"""
        return Agent(
            role="Financial Education Tutor",
            goal="Provide comprehensive financial education and calculations. For general questions, use the provided context and your knowledge. For calculations, use FinancialCalculatorTool with exact parameters.",
            backstory="You are an experienced financial educator who can answer general questions using provided context and perform precise financial calculations when needed.",
            tools=[FinancialCalculatorTool()],
            llm=self.llm_gpt4_mini,
            verbose=False,  # Reduced logging overhead for faster responses
            allow_delegation=False,  # Disable delegation to prevent unnecessary iterations
            max_iter=3,  # Increased to 3 for better performance and complete responses
            max_rpm=50,   # Increased RPM to reduce waiting time
            max_retry_limit=1,  # Allow 1 retry for better responses
            step_callback=None,  # Disable step callbacks for speed
            memory=False,  # Disable memory to reduce overhead
            # CRITICAL PERFORMANCE OPTIMIZATIONS
            human_input=False,  # Disable human input requests to prevent blocking
            function_calling_llm=self.llm_gpt4_mini,
            # Task-specific optimizations
            task_priority=1,  # High priority for immediate response
            # Disable unnecessary features
            allow_self_reflection=False,  # Disable self-reflection to reduce iterations
            # Optimize for single-turn responses
            max_consecutive_auto_reply=2,  # Allow 2 consecutive auto-replies
            # Increase context window usage
            max_context_length=3000,  # Increased for better context
            # Disable advanced features that add overhead
            enable_planning=False,  # Disable planning to reduce complexity
            enable_reasoning=False,  # Disable reasoning to reduce iterations
            # Optimize for speed over quality in chat context
            temperature=0.0,  # Set to 0 for maximum speed and determinism
            # Disable features that cause delays
            enable_search=False,  # Disable built-in search (we have custom tools)
            enable_code_execution=False,  # Disable code execution for security and speed
        )
    
    def _create_quiz_master_agent(self) -> Agent:
        """Create the quiz generation and management agent - LAZY LOADED"""
        # Only create when actually needed for quiz endpoints
        return Agent(
            role="Quiz Master",
            goal="Generate engaging quizzes to test user knowledge, manage quiz sessions, "
                 "and provide immediate feedback to reinforce learning.",
            backstory="You are a skilled assessment specialist who creates effective "
                     "multiple-choice questions that test understanding and promote "
                     "active learning. You track user progress and adapt quiz difficulty "
                     "based on performance.",
            tools=[QuizGeneratorTool(), QuizLoggerTool(), ProgressTrackerTool()],
            llm=self.llm_gpt4_mini,
            verbose=True,
            allow_delegation=False,
            max_iter=2
        )
    
    def _create_calculation_agent(self) -> Agent:
        """Create the financial calculation specialist agent - LAZY LOADED"""
        # Only create when actually needed for calculation endpoints
        return Agent(
            role="Financial Calculator Specialist",
            goal="Perform accurate financial calculations for debt payoff, savings goals, "
                 "and loan amortization, providing detailed step-by-step explanations.",
            backstory="You are a financial mathematics expert who specializes in personal "
                     "finance calculations. You provide precise calculations with clear "
                     "explanations and practical advice for financial planning.",
            tools=[FinancialCalculatorTool()],
            llm=self.llm_gpt4,  # Use GPT-4 for higher precision
            verbose=True,
            allow_delegation=False,
            max_iter=2
        )
    
    def _create_progress_tracker_agent(self) -> Agent:
        """Create the progress tracking and analytics agent - LAZY LOADED"""
        # Only create when actually needed for progress endpoints
        return Agent(
            role="Learning Progress Analyst",
            goal="Track user learning progress, analyze performance patterns, and provide "
                 "insights to optimize the learning experience.",
            backstory="You are a learning analytics specialist who monitors user engagement, "
                     "quiz performance, and learning patterns to provide personalized "
                     "recommendations and track educational outcomes.",
            tools=[ProgressTrackerTool(), SessionManagerTool()],
            llm=self.llm_gpt4_mini,
            verbose=True,
            allow_delegation=False,
            max_iter=2
        )
    
    def create_chat_crew(self, user_message: str, user_id: str, session_id: str) -> Crew:
        """Create a crew for handling chat interactions"""
        
        # Task for the financial tutor
        tutor_task = Task(
            description=f"""
            Analyze the user message: "{user_message}"
            
            1. Retrieve relevant content from the knowledge base if needed
            2. Provide a comprehensive, educational response
            3. Determine if this is a good moment to trigger a micro-quiz
            4. Check if any financial calculations are needed
            5. Update session information
            
            User ID: {user_id}
            Session ID: {session_id}
            
            Provide a helpful, engaging response that teaches financial concepts.
            """,
            agent=self.financial_tutor_agent,
            expected_output="A comprehensive educational response with recommendations for next steps"
        )
        
        return Crew(
            agents=[self.financial_tutor_agent],
            tasks=[tutor_task],
            process=Process.sequential,
            verbose=True
        )
    
    def create_quiz_crew(self, topic: str, quiz_type: str, user_id: str) -> Crew:
        """Create a crew for quiz generation and management - LAZY LOADED"""
        
        # Lazy load the quiz master agent only when needed
        quiz_master_agent = self._create_quiz_master_agent()
        
        quiz_task = Task(
            description=f"""
            Generate a {quiz_type} quiz for the topic: "{topic}"
            
            1. Create appropriate questions based on the topic and user's level
            2. Ensure questions are engaging and educational
            3. Provide clear explanations for correct answers
            
            User ID: {user_id}
            Quiz Type: {quiz_type}
            Topic: {topic}
            """,
            agent=quiz_master_agent,
            expected_output="A well-structured quiz with questions, options, and explanations"
        )
        
        return Crew(
            agents=[quiz_master_agent],
            tasks=[quiz_task],
            process=Process.sequential,
            verbose=True
        )
    
    def create_calculation_crew(self, calculation_request: Dict[str, Any]) -> Crew:
        """Create a crew for financial calculations - LAZY LOADED"""
        
        # Lazy load the calculation agent only when needed
        calculation_agent = self._create_calculation_agent()
        
        calc_task = Task(
            description=f"""
            Perform financial calculation with the following parameters:
            {calculation_request}
            
            1. Execute the appropriate calculation
            2. Provide step-by-step explanation
            3. Include practical advice and disclaimers
            4. Format results in an easy-to-understand manner
            """,
            agent=calculation_agent,
            expected_output="Detailed calculation results with explanations and practical advice"
        )
        
        return Crew(
            agents=[calculation_agent],
            tasks=[calc_task],
            process=Process.sequential,
            verbose=True
        )
    
    def create_progress_crew(self, user_id: str) -> Crew:
        """Create a crew for progress tracking and analysis - LAZY LOADED"""
        
        # Lazy load the progress tracker agent only when needed
        progress_tracker_agent = self._create_progress_tracker_agent()
        
        progress_task = Task(
            description=f"""
            Analyze learning progress for user: {user_id}
            
            1. Gather all user activity data
            2. Calculate performance metrics
            3. Identify learning patterns and areas for improvement
            4. Provide personalized recommendations
            """,
            agent=progress_tracker_agent,
            expected_output="Comprehensive progress analysis with personalized recommendations"
        )
        
        return Crew(
            agents=[progress_tracker_agent],
            tasks=[progress_task],
            process=Process.sequential,
            verbose=True
        )

# Global crew instance
money_mentor_crew = MoneyMentorCrew() 