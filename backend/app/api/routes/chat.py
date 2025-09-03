from fastapi import APIRouter, HTTPException, Depends, Request, Cookie
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import uuid
import time
import json
from fastapi.responses import StreamingResponse
import asyncio
from collections import OrderedDict


from app.core.config import settings
from app.core.auth import get_current_active_user
from app.core.database import get_supabase
from app.utils.session import (
    create_session,
    get_session,
    add_chat_message,
    add_quiz_response,
    update_progress,
    update_session,
    get_all_user_sessions,
    delete_session
)
from app.services.content_service import ContentService
from app.models.schemas import ChatMessageRequest
from app.services.chat_service import ChatService
from app.agents.function import money_mentor_function

router = APIRouter()
logger = logging.getLogger(__name__)
content_service = ContentService()

def get_chat_service() -> ChatService:
    """Get ChatService instance"""
    return ChatService()

@router.post("/message")
async def process_message(
    request: ChatMessageRequest,
    current_user: dict = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
) -> Dict[str, Any]:
    """Process a chat message and return the response"""
    start_time = time.time()
    print(f"\n🚀 CHAT ENDPOINT STARTED: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    
    try:
        # Step 1: ChatService instantiation timing
        step1_start = time.time()
        print(f"   📋 Step 1: ChatService instantiation...")
        
        # ChatService is already instantiated via dependency injection
        step1_time = time.time() - step1_start
        print(f"   ✅ Step 1 completed in {step1_time:.3f}s")
        
        # Step 2: Process message timing
        step2_start = time.time()
        print(f"   🤖 Step 2: Processing message with ChatService...")
        response = await chat_service.process_message(
            query=request.query,
            session_id=request.session_id,
            user_id=current_user["id"]
        )
        step2_time = time.time() - step2_start
        print(f"   ✅ Step 2 completed in {step2_time:.3f}s (ChatService processing)")
        
        # Step 3: Response validation timing
        step3_start = time.time()
        print(f"   🔍 Step 3: Validating response...")
        
        # Validate response
        if not isinstance(response, dict):
            raise HTTPException(status_code=500, detail="Invalid response format")
            
        # Ensure required fields
        if "message" not in response:
            raise HTTPException(status_code=500, detail="Missing message in response")
        
        step3_time = time.time() - step3_start
        print(f"   ✅ Step 3 completed in {step3_time:.3f}s (Response validation)")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        total_time = time.time() - start_time
        print(f"❌ CHAT ENDPOINT FAILED after {total_time:.3f}s: {e}")
        logger.error(f"Failed to process message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message/stream")
async def process_message_streaming(
    request: ChatMessageRequest,
    current_user: dict = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Process a chat message with streaming response for better UX"""
    start_time = time.time()
    print(f"\n🚀 CHAT STREAMING ENDPOINT STARTED: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    
    try:
        # Step 1: Get session and chat history (single fetch)
        print(f"   📋 Step 1: Getting session and chat history...")
        session = await get_session(request.session_id)
        if not session:
            # Create user message for initial chat history
            user_message = {
                "role": "user",
                "content": request.query,
                "timestamp": datetime.now().isoformat()
            }
            
            # Create session with initial user message
            session = await create_session(
                session_id=request.session_id, 
                user_id=current_user["id"],
                initial_chat_history=[user_message]
            )
            if not session:
                raise HTTPException(status_code=500, detail="Failed to create session for streaming")
            print(f"   ✅ Created new session: {session['session_id']} with initial user message")
        else:
            print(f"   ✅ Using existing session: {session['session_id']}")
        
        chat_history = session.get("chat_history", [])
        
        # Step 2: Get streaming response from LLM (single LLM call)
        print(f"   🔄 Step 2: Getting streaming response from LLM...")
        streaming_response = await money_mentor_function.process_and_stream(
            query=request.query,
            session_id=request.session_id,
            user_id=current_user["id"],
            skip_background_tasks=True,  # Skip background tasks in MoneyMentorFunction
            pre_fetched_session=session,  # Pass pre-fetched session to avoid duplicate fetch
            pre_fetched_history=chat_history  # Pass pre-fetched history to avoid duplicate fetch
        )
        
        # Step 3: Create a wrapper that collects the full response for background tasks
        print(f"   🔧 Step 3: Creating response wrapper for background tasks...")
        
        async def wrapped_streaming_response():
            collected_response = []
            
            # Get the original generator from the streaming response
            original_generator = streaming_response.body_iterator
            
            # Collect and yield tokens
            async for token in original_generator:
                collected_response.append(token.decode('utf-8'))
                yield token
            
            # After streaming is complete, handle background tasks
            full_response = ''.join(collected_response)
            
            # Handle background tasks with the complete response
            asyncio.create_task(chat_service._handle_background_tasks_only(
                query=request.query,
                session_id=request.session_id,
                user_id=current_user["id"],
                response_message=full_response,
                session=session,
                chat_history=chat_history
            ))
        
        # Return the wrapped streaming response
        final_response = StreamingResponse(
            wrapped_streaming_response(),
            media_type="text/plain",
            headers=streaming_response.headers
        )
        
        total_time = time.time() - start_time
        print(f"🏁 CHAT STREAMING ENDPOINT COMPLETED in {total_time:.3f}s")
        print(f"   ✅ Single LLM call with true streaming")
        print(f"   ✅ Background tasks handled after streaming completes")
        print(f"   ✅ No duplicate operations or database conflicts")
        
        return final_response
        
    except Exception as e:
        total_time = time.time() - start_time
        print(f"❌ CHAT STREAMING ENDPOINT FAILED after {total_time:.3f}s: {e}")
        logger.error(f"Failed to process streaming message: {e}")
        
        error_response = {
            "type": "error",
            "message": "I apologize, but I encountered an error processing your request. Please try again.",
            "session_id": request.session_id,
            "error": str(e)
        }
        
        return StreamingResponse(
            iter([f"data: {json.dumps(error_response)}\n\ndata: {json.dumps({'type': 'stream_end'})}\n\n"]),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )

@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    current_user: dict = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
) -> Dict[str, Any]:
    """Get chat history for a session"""
    try:
        session = await get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        chat_history = session.get("chat_history", [])
        
        return {
            "session_id": session_id,
            "chat_history": chat_history,
            "message_count": len(chat_history)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/history/{session_id}")
async def clear_chat_history(
    session_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Clear chat history for a session"""
    try:
        session = await get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
            
        # Update session with empty chat history (quiz history is now in centralized table)
        await update_session(session_id, {
            "chat_history": []
        })
        
        return {"status": "success", "message": "Chat history cleared"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/session/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Delete a chat session completely"""
    try:
        # Verify the session belongs to the current user
        session = await get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check if the session belongs to the current user
        if session.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied - session does not belong to current user")
        
        # Delete the session completely
        success = await delete_session(session_id)
        
        if success:
            return {
                "status": "success", 
                "message": f"Session {session_id} deleted successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete session")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/")
async def get_all_user_sessions_route(
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get all sessions for the authenticated user with their chat histories"""
    try:
        # Get all sessions for the current user using the helper function
        user_sessions = await get_all_user_sessions(current_user["id"])
        
        if not user_sessions:
            return {
                "success": True,
                "sessions": {},
                "total_sessions": 0,
                "total_messages": 0
            }
        
        # Create sessions object with session_id as keys
        # Use OrderedDict to maintain the order from the database query
        sessions = OrderedDict()
        total_messages = 0
        
        for session_data in user_sessions:
            # Get chat history from the session
            chat_history = session_data.get("chat_history", [])
            
            # Skip sessions with no chat history
            if not chat_history:
                continue
            
            # Sort chat history by timestamp to ensure chronological order
            sorted_chat_history = sorted(chat_history, key=lambda x: x.get("timestamp", ""))
            
            # Convert chat history to the required format
            formatted_messages = []
            for message in sorted_chat_history:
                role = message.get("role", "")
                content = message.get("content", "")
                
                # Format based on role
                if role.lower() == "user":
                    formatted_messages.append({"user": content})
                elif role.lower() in ["assistant", "ai"]:
                    formatted_messages.append({"assistant": content})
                else:
                    # Fallback for other roles
                    formatted_messages.append({role: content})
            
            # Only add sessions that have formatted messages
            if formatted_messages:
                # Use session_id as the key
                session_id = session_data["session_id"]
                sessions[session_id] = formatted_messages
                
                total_messages += len(formatted_messages)
        
        return {
            "success": True,
            "sessions": sessions,
            "total_sessions": len(sessions),
            "total_messages": total_messages,
            "user_id": current_user["id"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get user sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Performance endpoint removed - performance_monitor module not available 

@router.get("/session/{session_id}/chat-count")
async def get_session_chat_count(
    session_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get the number of chat messages in a session and whether a quiz should be generated"""
    try:
        session = await get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Count user messages in the session
        chat_history = session.get("chat_history", [])
        user_messages = [msg for msg in chat_history if msg.get("role") == "user"]
        chat_count = len(user_messages)
        
        # Determine if quiz should be generated (every 3 messages)
        should_generate_quiz = chat_count > 0 and chat_count % 3 == 0
        
        return {
            "session_id": session_id,
            "user_id": current_user["id"],
            "chat_count": chat_count,
            "should_generate_quiz": should_generate_quiz,
            "messages_until_quiz": (3 - (chat_count % 3)) if chat_count % 3 != 0 else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session chat count: {e}")
        raise HTTPException(status_code=500, detail="Failed to get session chat count") 

@router.get("/debug/list-session-ids")
async def list_session_ids():
    from app.core.database import get_supabase
    supabase = get_supabase()
    result = supabase.table("user_sessions").select("session_id").execute()
    return {"session_ids": [row["session_id"] for row in result.data]} 