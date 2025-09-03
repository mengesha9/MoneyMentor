# message_api.py
import time
import json
import logging
import asyncio
import re
from typing import Dict, Any, List, AsyncIterable, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI

from app.core.config import settings
from app.services.calculation_service import CalculationService
from app.services.content_service import ContentService
from app.utils.session import get_session, create_session
from app.utils.user_validation import require_authenticated_user_id, sanitize_user_id_for_logging

# Initialize logging
logger = logging.getLogger(__name__)

# Configure OpenAI client
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Define calculator functions for OpenAI function-calling
calculator_functions = [
    {
        "type": "function",
        "function": {
            "name": "credit_card_payoff",
            "description": "Calculate credit card payoff timeline",
            "parameters": {
                "type": "object",
                "properties": {
                    "balance": {"type": "number"},
                    "apr": {"type": "number"},
                    "monthly_payment": {"type": ["number", "null"]},
                    "target_months": {"type": ["integer", "null"]}
                },
                "required": ["balance", "apr"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "savings_goal",
            "description": "Calculate monthly savings needed for a goal",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_amount": {"type": "number"},
                    "target_months": {"type": "integer"},
                    "current_savings": {"type": "number"},
                    "interest_rate": {"type": "number"}
                },
                "required": ["target_amount", "target_months"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "student_loan_amortization",
            "description": "Calculate student loan amortization schedule",
            "parameters": {
                "type": "object",
                "properties": {
                    "principal": {"type": "number"},
                    "apr": {"type": "number"},
                    "target_months": {"type": "integer"},
                    "monthly_payment": {"type": ["number", "null"]}
                },
                "required": ["principal", "apr", "target_months"]
            }
        }
    }
]

class MoneyMentorFunction:
    """Service for handling chat interactions with direct OpenAI function-calling and streaming"""
    
    def __init__(self):
        self.system_prompt = """You are MoneyMentor, a friendly and knowledgeable financial education tutor. Your role is to:

        1. Help users understand financial concepts in simple, clear terms
        2. Provide educational content about personal finance, budgeting, investing, and debt management
        3. Answer questions about financial terms and concepts
        4. Guide users through financial calculations when they ask for them
        5. Be encouraging and supportive while maintaining accuracy

        Key guidelines:
        - ALWAYS keep your responses extremely short, concise, and to the point
        - NEVER exceed 400 words in your response
        - Use simple language to explain complex concepts
        - Provide practical, actionable advice when appropriate
        - Be encouraging and supportive
        - If a user asks for a calculation, use the available functions to help them
        - Always include a disclaimer that estimates are for educational purposes only
        - Focus on the most important information first
        - Avoid unnecessary explanations, repetition, or filler
        - Use bullet points or numbered lists when appropriate for clarity
        - If you can answer in fewer words, do so
        - If a list or table is clearer, use it

        Remember: You're here to educate and empower users with financial knowledge. Be helpful but as brief as possible."""
        self.calc_service = CalculationService()
        self.content_service = ContentService()

    async def _save_history(self, session_id: str, role: str, content: str, user_id: str = None) -> None:
        """Append a message to session chat history"""
        try:
            # Validate user_id is a real UUID from authentication
            validated_user_id = require_authenticated_user_id(user_id, "history saving")
            sanitized_user_id = sanitize_user_id_for_logging(validated_user_id)
            
            # Get existing session
            session = await get_session(session_id)
            if not session:
                # Create new session if it doesn't exist
                # For new sessions, we'll create it with the current message
                initial_message = {
                    "role": role,
                    "content": content,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                session = await create_session(
                    session_id=session_id,  # Use the provided session_id
                    user_id=validated_user_id,
                    initial_chat_history=[initial_message]
                )
                # Use the generated session_id from the new session
                session_id = session["session_id"]
                print(f"💾 DEBUG: Created new session {session_id} with initial {role} message")
            else:
                # Session exists, append the message
                chat_history = session.get("chat_history", [])
                chat_history.append({
                    "role": role,
                    "content": content,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                # Update session with new chat history
                from app.utils.session import update_session
                await update_session(session_id, {"chat_history": chat_history})
                print(f"💾 DEBUG: Added {role} message to existing session {session_id}")
            
        except Exception as e:
            print(f"❌ ERROR: Failed to save history: {e}")
            logger.error(f"Failed to save history: {e}")

    def _format_chat_history(self, history: List[Dict[str, Any]]) -> str:
        return "\n".join(f"{m['role']}: {m['content']}" for m in history)

    async def process_message(
        self,
        message: str,
        chat_history: List[Dict[str, str]],
        session_id: str,
        user_id: Optional[str] = None,
        skip_session_fetch: bool = False
    ) -> Dict[str, Any]:
        """Process a message and return a response - this is what chat_service.py expects"""
        try:
            # Get session and chat history (skip if already provided by ChatService)
            if skip_session_fetch:
                # Use provided chat_history directly, no need to fetch session
                session = None
            else:
                # Get session and chat history
                session = await get_session(session_id)
                if not session:
                    # Create new session and use the generated session_id
                    # Validate user_id is a real UUID from authentication
                    validated_user_id = require_authenticated_user_id(user_id, "session creation in process_message")
                    
                    # Create initial user message
                    initial_message = {
                        "role": "user",
                        "content": message,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    
                    session = await create_session(
                        session_id=session_id,  # Use the provided session_id
                        user_id=validated_user_id,
                        initial_chat_history=[initial_message]
                    )
                    session_id = session["session_id"]  # Update session_id to use generated one
                
                if not session:
                    raise HTTPException(status_code=500, detail="Failed to create session")

                # Use provided chat_history or get from session
                if not chat_history:
                    chat_history = session.get("chat_history", [])

            # Get relevant content context
            content_items = await self.content_service.search_content(message, limit=2, threshold=0.2)
            context_str = "\n".join(item.get('content','')[:200] for item in content_items or [])
            
            # DEBUG: Print context and chat history
            print(f"\n🔍 DEBUG - Context from Vector Store:")
            print(f"Content items found: {len(content_items) if content_items else 0}")
            if content_items:
                for i, item in enumerate(content_items):
                    print(f"  Item {i+1}: {item.get('content', '')[:100]}...")
            else:
                print("  No content items found")
            
            print(f"\n🔍 DEBUG - Chat History:")
            print(f"Chat history length: {len(chat_history)}")
            if chat_history:
                for i, msg in enumerate(chat_history[-3:]):  # Show last 3 messages
                    print(f"  {msg.get('role', 'unknown')}: {msg.get('content', '')[:100]}...")
            else:
                print("  No chat history found")
            
            print(f"\n🔍 DEBUG - Final Context String:")
            print(f"Context string length: {len(context_str)}")
            print(f"Context: {context_str[:200]}...")
            print("=" * 80)

            # Detect calculation intent
            calc_patterns = [
                r"how\s+much\s+(?:do\s+I\s+need\s+to\s+)?(?:pay|save|contribute)",  # "how much do I need to pay"
                r"how\s+long\s+(?:will\s+it\s+take\s+to\s+)?(?:pay\s+off|clear|reach)",  # "how long will it take to pay off"
                r"(?:pay\s+off|clear)\s+\$\d+",  # "pay off $6000"
                r"\d+\s*(?:months?|years?)\s+(?:to\s+)?(?:pay\s+off|clear|reach)",  # "12 months to pay off"
                r"monthly\s+payment\s+(?:of\s+)?\$\d+",  # "monthly payment of $500"
                r"\$\d+\s+(?:per\s+)?month",  # "$500 per month"
                r"calculate\s+(?:my|the)",  # "calculate my payment"
                r"what\s+(?:would\s+be\s+)?(?:my|the)\s+(?:monthly\s+)?payment",  # "what would be my payment"
            ]
            
            # Exclude educational questions that mention money but don't need calculations
            educational_patterns = [
                r"what\s+are\s+(?:some\s+)?ways?\s+to",  # "what are some ways to pay"
                r"how\s+can\s+I",  # "how can I pay"
                r"what\s+options?\s+(?:do\s+I\s+have|are\s+available)",  # "what options do I have"
                r"explain\s+(?:how\s+)?(?:to|about)",  # "explain how to pay"
                r"tell\s+me\s+about",  # "tell me about paying"
                r"what\s+is\s+",  # "what is a loan"
                r"how\s+does\s+",  # "how does APR work"
            ]
            
            # Check if it's a calculation request
            is_calc_request = any(re.search(p, message.lower()) for p in calc_patterns)
            
            # Check if it's an educational question (even if it mentions money)
            is_educational = any(re.search(p, message.lower()) for p in educational_patterns)
            
            # Only treat as calculation if it's explicitly a calculation request AND not an educational question
            is_calc = is_calc_request and not is_educational

            # Build messages for OpenAI
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            if context_str:
                messages.append({"role": "system", "content": f"Relevant context: {context_str}"})
            messages.extend(chat_history)
            messages.append({"role": "user", "content": message})

            # Handle calculation requests
            if is_calc:
                return await self._handle_calculation_request(message, messages, session_id, user_id or "default_user", skip_history_save=skip_session_fetch)
            else:
                return await self._handle_general_chat(message, messages, session_id, user_id or "default_user", skip_history_save=skip_session_fetch)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "message": "I apologize, but I encountered an error processing your message. Please try again.",
                "session_id": session_id,
                "error": str(e)
            }

    async def _handle_calculation_request(self, message: str, messages: List[Dict], session_id: str, user_id: str = None, skip_history_save: bool = False) -> Dict[str, Any]:
        """Handle calculation requests with function calling"""
        try:
            # Phase 1: Function calling to extract parameters
            response1 = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=calculator_functions,
                tool_choice="auto",
                temperature=0.0
            )

            # Check if function was called
            if response1.choices[0].finish_reason == "tool_calls":
                tool_call = response1.choices[0].message.tool_calls[0]
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                # Perform calculation using the calculation service
                calc_result = await self.calc_service.calculate(function_name, function_args)

                # Phase 2: Generate plain English explanation with financial literacy concepts
                explanation_prompt = f"""Using the plan below, provide a concise explanation in plain English.

                Calculation Result:
                {json.dumps(calc_result, indent=2)}

                STRICT INSTRUCTIONS:
                - Your response MUST be extremely short, concise, and never exceed 400 words.
                - Focus only on the most important points and actionable insights.
                - Use bullet points or numbered lists if possible.
                - Avoid any unnecessary explanation, repetition, or filler.
                - End with: Estimates only. Verify with a certified financial professional.

                """

                explanation_messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": explanation_prompt}
                ]

                response2 = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=explanation_messages,
                    temperature=0.3,
                    max_tokens=500,  # Limit to ~400-500 words
                    stream=True
                )

                explanation = response2.choices[0].message.content

                # Save to history in background (user gets response immediately)
                if not skip_history_save:
                    # Validate user_id is a real UUID
                    validated_user_id = require_authenticated_user_id(user_id, "calculation history saving")
                    asyncio.create_task(self._save_history(session_id, "user", message, validated_user_id))
                    asyncio.create_task(self._save_history(session_id, "assistant", explanation, validated_user_id))

                return {
                    "message": explanation,
                    "session_id": session_id,
                    "is_calculation": True,
                    "calculation_result": calc_result
                }
            else:
                # No function call - treat as general chat
                return await self._handle_general_chat(message, messages, session_id, user_id, skip_history_save=skip_history_save)

        except Exception as e:
            logger.error(f"Calculation handling failed: {e}")
            return {
                "message": "I apologize, but I encountered an error processing your calculation request. Please check your input and try again.",
                "session_id": session_id,
                "error": str(e)
            }

    async def _handle_general_chat(self, message: str, messages: List[Dict], session_id: str, user_id: str = None, skip_history_save: bool = False) -> Dict[str, Any]:
        """Handle general chat requests"""
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.3,
                max_tokens=400,  # Limit to ~400-500 words
                stream=True
            )

            assistant_message = response.choices[0].message.content

            # Save to history in background (user gets response immediately)
            if not skip_history_save:
                # Validate user_id is a real UUID
                validated_user_id = require_authenticated_user_id(user_id, "general chat history saving")
                asyncio.create_task(self._save_history(session_id, "user", message, validated_user_id))
                asyncio.create_task(self._save_history(session_id, "assistant", assistant_message, validated_user_id))

            return {
                "message": assistant_message,
                "session_id": session_id,
                "is_calculation": False
            }

        except Exception as e:
            logger.error(f"General chat handling failed: {e}")
            return {
                "message": "I apologize, but I encountered an error processing your message. Please try again.",
                "session_id": session_id,
                "error": str(e)
            }

    async def process_and_stream(
        self,
        query: str,
        session_id: str,
        user_id: Optional[str] = None,
        skip_background_tasks: bool = False,
        pre_fetched_session: Optional[Dict] = None,
        pre_fetched_history: Optional[List[Dict]] = None
    ) -> StreamingResponse:
        """Streaming version for real-time responses"""
        # Session management (use pre-fetched if available)
        if pre_fetched_session and pre_fetched_history:
            session = pre_fetched_session
            history = pre_fetched_history
        else:
            # Fallback to fetching session and history
            session = await get_session(session_id)
            if not session:
                # Create new session and use the generated session_id
                # Validate user_id is a real UUID from authentication
                validated_user_id = require_authenticated_user_id(user_id, "streaming session creation")
                session = await create_session(
                    session_id=session_id,  # Use the provided session_id
                    user_id=validated_user_id
                )
            
            if not session:
                raise HTTPException(status_code=500, detail="Failed to create session")
            history = session.get("chat_history", [])

        # Detect calculation intent with more precise patterns
        # Look for specific calculation request patterns, not just dollar amounts
        calc_patterns = [
            r"how\s+much\s+(?:do\s+I\s+need\s+to\s+)?(?:pay|save|contribute)",  # "how much do I need to pay"
            r"how\s+long\s+(?:will\s+it\s+take\s+to\s+)?(?:pay\s+off|clear|reach)",  # "how long will it take to pay off"
            r"(?:pay\s+off|clear)\s+\$\d+",  # "pay off $6000"
            r"\d+\s*(?:months?|years?)\s+(?:to\s+)?(?:pay\s+off|clear|reach)",  # "12 months to pay off"
            r"monthly\s+payment\s+(?:of\s+)?\$\d+",  # "monthly payment of $500"
            r"\$\d+\s+(?:per\s+)?month",  # "$500 per month"
            r"calculate\s+(?:my|the)",  # "calculate my payment"
            r"what\s+(?:would\s+be\s+)?(?:my|the)\s+(?:monthly\s+)?payment",  # "what would be my payment"
        ]
        
        # Exclude educational questions that mention money but don't need calculations
        educational_patterns = [
            r"what\s+are\s+(?:some\s+)?ways?\s+to",  # "what are some ways to pay"
            r"how\s+can\s+I",  # "how can I pay"
            r"what\s+options?\s+(?:do\s+I\s+have|are\s+available)",  # "what options do I have"
            r"explain\s+(?:how\s+)?(?:to|about)",  # "explain how to pay"
            r"tell\s+me\s+about",  # "tell me about paying"
            r"what\s+is\s+",  # "what is a loan"
            r"how\s+does\s+",  # "how does APR work"
        ]
        
        # Check if it's a calculation request
        is_calc_request = any(re.search(p, query.lower()) for p in calc_patterns)
        
        # Check if it's an educational question (even if it mentions money)
        is_educational = any(re.search(p, query.lower()) for p in educational_patterns)
        
        # Only treat as calculation if it's explicitly a calculation request AND not an educational question
        is_calc = is_calc_request and not is_educational

        # Optional content retrieval
        content_items = await self.content_service.search_content(query, limit=2, threshold=0.2)
        context_str = "\n".join(item.get('content','')[:200] for item in content_items or [])
        
        # DEBUG: Print context and chat history for streaming
        print(f"\n🔍 DEBUG STREAMING - Context from Vector Store:")
        print(f"Content items found: {len(content_items) if content_items else 0}")
        if content_items:
            for i, item in enumerate(content_items):
                print(f"  Item {i+1}: {item.get('content', '')[:100]}...")
        else:
            print("  No content items found")
        
        print(f"\n🔍 DEBUG STREAMING - Chat History:")
        print(f"Chat history length: {len(history)}")
        if history:
            for i, msg in enumerate(history[-3:]):  # Show last 3 messages
                print(f"  {msg.get('role', 'unknown')}: {msg.get('content', '')[:100]}...")
        else:
            print("  No chat history found")
        
        print(f"\n🔍 DEBUG STREAMING - Final Context String:")
        print(f"Context string length: {len(context_str)}")
        print(f"Context: {context_str[:200]}...")
        print("=" * 80)

        # Build base messages
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        if context_str:
            messages.append({"role": "system", "content": context_str})
        messages.extend(history)
        messages.append({"role": "user", "content": query})

        # Generator for streaming tokens
        async def token_generator():
            # Phase 1: Function-calling for calculations
            if is_calc:
                try:
                    resp1 = await client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        tools=calculator_functions,
                        tool_choice="auto",
                        stream=True
                    )
                    
                    # Collect function call
                    fn_name = None
                    fn_args_str = ""
                    async for chunk in resp1:
                        if chunk.choices[0].delta.tool_calls:
                            tool_call = chunk.choices[0].delta.tool_calls[0]
                            if tool_call.function:
                                if tool_call.function.name:
                                    fn_name = tool_call.function.name
                                if tool_call.function.arguments:
                                    fn_args_str += tool_call.function.arguments
                    
                    # Parse function arguments after collecting complete JSON
                    fn_args = None
                    if fn_name and fn_args_str:
                        try:
                            fn_args = json.loads(fn_args_str)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse function arguments: {fn_args_str}, error: {e}")
                            # Fall back to non-streaming approach for calculations
                            response = await self._handle_calculation_request(query, messages, session_id, user_id or "default_user", skip_history_save=skip_background_tasks)
                            yield response.get("message", "Error processing calculation").encode("utf-8")
                            return
                    
                    if fn_name and fn_args is not None:
                        calc_result = await self.calc_service.calculate(fn_name, fn_args)
                        
                        # Phase 2: Generate plain English explanation with financial literacy concepts
                        explanation_prompt = f"""Using the plan below, provide a concise explanation in plain English.

                        Calculation Result:
                        {json.dumps(calc_result, indent=2)}

                        STRICT INSTRUCTIONS:
                        - Your response MUST be extremely short, concise, and never exceed 400 words.
                        - Focus only on the most important points and actionable insights.
                        - Use bullet points or numbered lists if possible.
                        - Avoid any unnecessary explanation, repetition, or filler.
                        - End with: Estimates only. Verify with a certified financial professional.

                        """

                        explanation_messages = [
                            {"role": "system", "content": self.system_prompt},
                            {"role": "user", "content": explanation_prompt}
                        ]
                        
                        # Phase 2: Explanation stream
                        resp2 = await client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=explanation_messages,
                            temperature=0.4,
                            max_tokens=400,  # Limit to ~400-500 words
                            stream=True
                        )
                        async for chunk in resp2:
                            if chunk.choices[0].delta.content:
                                yield chunk.choices[0].delta.content.encode("utf-8")
                    else:
                        # No function call detected, fall back to general chat
                        response = await self._handle_general_chat(query, messages, session_id, user_id or "default_user", skip_history_save=skip_background_tasks)
                        yield response.get("message", "Error processing request").encode("utf-8")
                        
                except Exception as e:
                    logger.error(f"Streaming calculation failed: {e}")
                    yield f"Error processing calculation: {str(e)}".encode("utf-8")
            else:
                # General chat streaming
                resp = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.4,
                    max_tokens=400,  # Limit to ~400-500 words
                    stream=True
                )
                async for chunk in resp:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content.encode("utf-8")

        # Only save history if background tasks are not being handled by ChatService
        if not skip_background_tasks:
            # Fire-and-forget history saves in background (user gets response immediately)
            asyncio.create_task(self._save_history(session_id, "user", query, user_id or "default_user"))
            # Use a simple generator that saves assistant response in background
            async def wrapped_generator():
                collected = []
                async for token in token_generator():
                    collected.append(token.decode('utf-8'))
                    yield token
                full_response = ''.join(collected)
                # Save assistant response in background
                asyncio.create_task(self._save_history(session_id, "assistant", full_response, user_id or "default_user"))
            
            return StreamingResponse(wrapped_generator(), media_type="text/plain")
        else:
            # Skip history saving since ChatService handles it
            return StreamingResponse(token_generator(), media_type="text/plain")

# Create a singleton instance
money_mentor_function = MoneyMentorFunction()

