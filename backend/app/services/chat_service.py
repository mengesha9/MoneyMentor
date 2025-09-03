from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timezone
import uuid
import time
import asyncio
import json
from fastapi import HTTPException
from app.agents.function import money_mentor_function
from app.services.engagement_service import EngagementService

from app.utils.session import get_session, create_session, add_chat_message, add_quiz_response, update_progress
from app.services.google_sheets_service import GoogleSheetsService
from app.utils.hybrid_memory_manager import hybrid_memory_manager

logger = logging.getLogger(__name__)

class ChatService:
    """Service for handling chat interactions with optimized background processing"""
    
    def __init__(self):
        self.sheets_service = GoogleSheetsService()
        self.engagement_service = None  # Initialize lazily to avoid circular imports
    
    async def process_message(
        self,
        query: str,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a chat message and return the response with optimized background processing"""
        service_start_time = time.time()
        print(f"      🔧 ChatService.process_message() started")
        
        try:
            # Step 1: Session management (CRITICAL - must be synchronous)
            step1_start = time.time()
            print(f"         📋 Step 1.1: Getting/creating session...")
            session = await get_session(session_id)
            if not session:
                try:
                    # Create user message for initial chat history
                    user_message = {
                        "role": "user",
                        "content": query,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    
                    # Create session with initial user message
                    session = await create_session(
                        user_id=user_id,
                        initial_chat_history=[user_message]
                    )
                    session_id = session["session_id"]  # Update session_id to use generated one
                    if not session:
                        raise HTTPException(status_code=500, detail="Failed to create session")
                    logger.info(f"Created new session: {session_id} with initial user message")
                except Exception as e:
                    logger.error(f"Failed to create session: {e}")
                    raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")
            else:
                # Session exists, create user message for background processing
                user_message = {
                    "role": "user",
                    "content": query,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            step1_time = time.time() - step1_start
            print(f"         ✅ Step 1.1 completed in {step1_time:.3f}s (Session management)")
            
            # Step 2: Essential memory operations (CRITICAL - needed for context)
            step2_start = time.time()
            print(f"         🧠 Step 1.2: Essential memory operations...")
            
            # Use provided user_id or fall back to session user_id or session_id
            user_id = user_id or session.get("user_id", session_id)
            
            # Get chat history from session to pass to MoneyMentorFunction
            chat_history = session.get("chat_history", [])
            
            step2_time = time.time() - step2_start
            print(f"         ✅ Step 1.2 completed in {step2_time:.3f}s (Essential memory operations - OPTIMIZED)")
            
            # Step 3: OpenAI processing with PARALLEL optimization (MAIN BOTTLENECK - must be synchronous)
            step3_start = time.time()
            print(f"         🤖 Step 1.3: OpenAI processing with PARALLEL optimization...")
            try:
                response = await money_mentor_function.process_message(
                    message=query,
                    chat_history=chat_history,  # Pass the already-fetched chat history
                    session_id=session_id,
                    user_id=user_id,
                    skip_session_fetch=True  # Tell MoneyMentorFunction to skip session fetching
                )
                
                # Ensure response is a dictionary
                if response is None:
                    response = {"message": "I apologize, but I couldn't generate a response."}
                elif not isinstance(response, dict):
                    response = {"message": str(response)}
                
                # Ensure message field exists
                if "message" not in response:
                    response["message"] = "I apologize, but I couldn't generate a proper response."
                
            except Exception as openai_error:
                logger.error(f"OpenAI processing failed: {openai_error}")
                response = {
                    "message": "I apologize, but I encountered an error processing your message. Please try again.",
                    "error": str(openai_error)
                }
            
            step3_time = time.time() - step3_start
            print(f"         ✅ Step 1.3 completed in {step3_time:.3f}s (OpenAI processing with PARALLEL optimization)")
            
            # Step 4: Add session_id to response (CRITICAL - must be synchronous)
            response["session_id"] = session_id
            
            # Add calculation detection to response
            response["is_calculation"] = self._is_calculation_request(query)
            
            # Step 5: ALL background tasks (NONE are critical for immediate response)
            step5_start = time.time()
            print(f"         🔄 Step 1.5: ALL background tasks (NONE critical for response)...")
            
            # ALL tasks are background - user gets response immediately
            background_tasks = []
            
            # Background Task 1: Chat history updates (for future context)
            background_tasks.append(self._background_chat_history(
                session_id, user_id, user_message, response["message"]
            ))
            
            # Background Task 2: Progress updates (if needed)
            if response.get("progress"):
                background_tasks.append(self._background_progress_update(session_id, response["progress"]))
            
            # Background Task 3: Quiz handling (if needed)
            if response.get("quiz"):
                background_tasks.append(self._background_quiz_handling(session_id, response["quiz"]))
            
            # Background Task 4: Analytics and logging (with aggressive timeouts)
            background_tasks.append(self._background_analytics(
                user_id, session_id, query, response["message"]
            ))
            
            # Background Task 5: Hybrid memory operations (vector DB - very expensive)
            background_tasks.append(self._background_hybrid_memory(
                user_id, session_id, user_message, response["message"]
            ))
            
            # Fire-and-forget ALL background tasks
            for task in background_tasks:
                asyncio.create_task(task)
            
            step5_time = time.time() - step5_start
            print(f"         ✅ Step 1.5 completed in {step5_time:.3f}s (ALL background tasks - user gets response immediately)")
            
            # Total ChatService timing
            service_total_time = time.time() - service_start_time
            print(f"      🏁 ChatService completed in {service_total_time:.3f}s")
            print(f"         📊 ChatService Breakdown:")
            print(f"            - Session management: {step1_time:.3f}s ({(step1_time/service_total_time)*100:.1f}%)")
            print(f"            - Essential memory: {step2_time:.3f}s ({(step2_time/service_total_time)*100:.1f}%)")
            print(f"            - OpenAI (PARALLEL): {step3_time:.3f}s ({(step3_time/service_total_time)*100:.1f}%)")
            print(f"            - Background tasks: {step5_time:.3f}s ({(step5_time/service_total_time)*100:.1f}%)")
            
            # Performance analysis
            if response.get("is_calculation"):
                print(f"         🧮 CALCULATION REQUEST detected - optimized processing used")
            else:
                print(f"         💬 GENERAL CHAT REQUEST - standard processing used")
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process message: {str(e)}"
            )
    
    async def _background_chat_history(self, session_id: str, user_id: str, user_message: Dict, assistant_message: str):
        """Background chat history updates - for future context"""
        try:
            # Get current session to check if user message is already there
            session = await get_session(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found for chat history update")
                return
                
            chat_history = session.get("chat_history", [])
            
            # Check if user message is already in chat history (for new sessions)
            user_message_exists = any(
                msg.get("role") == "user" and msg.get("content") == user_message.get("content")
                for msg in chat_history
            )
            
            # Only add user message if it's not already there
            if not user_message_exists:
                await add_chat_message(session_id, user_message)
            
            # Always add assistant response to chat history
            assistant_msg = {
                "role": "assistant",
                "content": assistant_message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await add_chat_message(session_id, assistant_msg)
            
            logger.info(f"Background chat history completed for session {session_id}")
            
        except Exception as e:
            logger.warning(f"Background chat history failed for session {session_id}: {e}")
    
    async def _background_progress_update(self, session_id: str, progress: Dict[str, Any]):
        """Background progress update - for future context"""
        try:
            await update_progress(session_id, progress)
            logger.info(f"Background progress update completed for session {session_id}")
        except Exception as e:
            logger.warning(f"Background progress update failed for session {session_id}: {e}")
    
    async def _background_quiz_handling(self, session_id: str, quiz_data: Dict[str, Any]):
        """Background quiz handling - for future context"""
        try:
            quiz_id = str(uuid.uuid4())
            if isinstance(quiz_data, dict) and "questions" in quiz_data:
                await add_quiz_response(session_id, {
                    "quiz_id": quiz_id,
                    "questions": quiz_data["questions"]
                })
                logger.info(f"Background quiz handling completed for session {session_id}")
        except Exception as e:
            logger.warning(f"Background quiz handling failed for session {session_id}: {e}")
    
    async def _background_analytics(self, user_id: str, session_id: str, query: str, response: str):
        """Background analytics and logging - for future context with aggressive timeout"""
        try:
            # Google Sheets logging with very short timeout
            chat_log_data = {
                "user_id": user_id,
                "session_id": session_id,
                "message_type": "user",
                "message": query,
                "response": response
            }
            
            # Set very short timeout for Google Sheets logging
            await asyncio.wait_for(
                self.sheets_service.log_chat_message(chat_log_data),
                timeout=0.5  # Reduced from 1.0 to 0.5 seconds
            )
            
            # Engagement tracking with shorter timeout
            if self.engagement_service is None:
                self.engagement_service = EngagementService()
            
            await asyncio.wait_for(
                self.engagement_service.track_session_engagement(user_id, session_id),
                timeout=0.8  # Reduced from 1.5 to 0.8 seconds
            )
            
            logger.info(f"Background analytics completed for user {user_id}")
            
        except asyncio.TimeoutError:
            logger.warning(f"Background analytics timed out for user {user_id} - this is normal and doesn't affect the response")
        except Exception as e:
            logger.warning(f"Background analytics failed for user {user_id}: {e} - this doesn't affect the response")
    
    async def _background_hybrid_memory(self, user_id: str, session_id: str, user_message: Dict, assistant_message: str):
        """Background hybrid memory operations - for future context with aggressive timeout"""
        try:
            # Add user message to hybrid memory with timeout
            await asyncio.wait_for(
                hybrid_memory_manager.add_to_memory(user_message, user_id, session_id),
                timeout=0.3  # Very short timeout for vector DB operations
            )
            
            # Add assistant response to hybrid memory with timeout
            await asyncio.wait_for(
                hybrid_memory_manager.add_to_memory(
                    {
                        "role": "assistant",
                        "content": assistant_message,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    user_id,
                    session_id
                ),
                timeout=0.3  # Very short timeout for vector DB operations
            )
            
            logger.info(f"Background hybrid memory operations completed for session {session_id}")
            
        except asyncio.TimeoutError:
            logger.warning(f"Background hybrid memory operations timed out for session {session_id} - this is normal")
        except Exception as e:
            logger.warning(f"Background hybrid memory operations failed for session {session_id}: {e}")
    
    async def process_calculation_streaming(self, query: str, session_id: str):
        """Process calculation requests with streaming response for better UX"""
        try:
            # Quick calculation detection
            if not self._is_calculation_request(query):
                # Not a calculation request - yield an error and return
                yield {
                    "type": "calculation_error",
                    "message": "This is not a calculation request. Please ask a calculation question.",
                    "session_id": session_id
                }
                return
            
            # Start streaming response
            yield {
                "type": "calculation_start",
                "message": "Processing your calculation request...",
                "session_id": session_id
            }
            
            # Extract parameters (fast operation)
            params = self._extract_calculation_params(query)
            if not params:
                yield {
                    "type": "calculation_error",
                    "message": "I couldn't extract the calculation parameters. Please provide specific amounts, rates, and timeframes.",
                    "session_id": session_id
                }
                return
            
            yield {
                "type": "calculation_progress",
                "message": "Extracting calculation parameters...",
                "session_id": session_id
            }
            
            # Determine calculation type
            calculation_type = self._determine_calculation_type(query)
            
            yield {
                "type": "calculation_progress",
                "message": f"Performing {calculation_type.replace('_', ' ')} calculation...",
                "session_id": session_id
            }
            
            # Perform calculation
            from app.services.calculation_service import CalculationService
            calc_service = CalculationService()
            result = await calc_service.calculate(calculation_type, params)
            
            # Format response
            formatted_response = f"""Here is your calculation result:
```json
{json.dumps(result, indent=2)}
```

Based on the calculation results, your 'monthly_payment' would be ${result.get('monthly_payment', 'N/A')}. The 'months_to_payoff' shows it will take {result.get('months_to_payoff', 'N/A')} months to clear the debt or reach your goal. The 'total_interest' you'll pay or earn is ${result.get('total_interest', 'N/A')}. Following the 'step_by_step_plan' will help you stay on track.

Estimates only. Verify with a certified financial professional."""
            
            yield {
                "type": "calculation_complete",
                "message": formatted_response,
                "session_id": session_id,
                "calculation_result": result
            }
            
        except Exception as e:
            logger.error(f"Calculation streaming failed: {e}")
            yield {
                "type": "calculation_error",
                "message": "I encountered an error processing your calculation request. Please check your input and try again.",
                "session_id": session_id
            }
    
    def _is_calculation_request(self, message: str) -> bool:
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
        
        # Log extracted parameters for debugging
        if params:
            logger.info(f"Extracted calculation parameters: {params}")
        else:
            logger.warning(f"No parameters extracted from message: '{message}'")
        
        return params
    
    def _determine_calculation_type(self, message: str) -> str:
        """Determine calculation type based on message content"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['credit', 'card', 'payoff']):
            return 'credit_card_payoff'
        elif any(word in message_lower for word in ['savings', 'goal', 'save']):
            return 'savings_goal'
        elif any(word in message_lower for word in ['student', 'loan', 'borrow']):
            return 'student_loan'
        else:
            return 'credit_card_payoff'
    
    async def _handle_background_tasks_only(
        self,
        query: str,
        session_id: str,
        user_id: str,
        response_message: str,
        session: Dict[str, Any],
        chat_history: List[Dict[str, Any]]
    ):
        """Handle background tasks only (for streaming endpoint)"""
        try:
            # Create user message
            user_message = {
                "role": "user",
                "content": query,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Create assistant message
            assistant_message = {
                "role": "assistant",
                "content": response_message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # ALL background tasks (fire-and-forget)
            background_tasks = []
            
            # Background Task 1: Chat history updates (for future context)
            background_tasks.append(self._background_chat_history(
                session_id, user_id, user_message, response_message
            ))
            
            # Background Task 2: Analytics and logging (with aggressive timeouts)
            background_tasks.append(self._background_analytics(
                user_id, session_id, query, response_message
            ))
            
            # Background Task 3: Hybrid memory operations (vector DB - very expensive)
            background_tasks.append(self._background_hybrid_memory(
                user_id, session_id, user_message, response_message
            ))
            
            # Fire-and-forget ALL background tasks
            for task in background_tasks:
                asyncio.create_task(task)
                
            logger.info(f"Background tasks initiated for streaming session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to handle background tasks for streaming: {e}") 