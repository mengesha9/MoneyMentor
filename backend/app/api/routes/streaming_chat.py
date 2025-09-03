from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, Optional, AsyncGenerator
import logging
import json
import time
import asyncio
from datetime import datetime

from app.agents.function import money_mentor_function
from app.core.config import settings
from app.core.auth import get_current_active_user
from app.utils.session import (
    create_session,
    get_session,
    add_chat_message,
    update_session
)
from app.services.content_service import ContentService
from app.models.schemas import ChatMessageRequest
from app.services.chat_service import ChatService

router = APIRouter()
logger = logging.getLogger(__name__)
content_service = ContentService()

def get_chat_service() -> ChatService:
    """Get ChatService instance"""
    return ChatService()

@router.post("/stream")
async def process_message_streaming(
    request: ChatMessageRequest,
    current_user: dict = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Process a chat message with streaming response using FastAPI StreamingResponse.
    
    This endpoint demonstrates Option A: FastAPI StreamingResponse approach.
    It uses the same services as the regular chat endpoint but provides
    streaming responses for better user experience.
    """
    start_time = time.time()
    print(f"\n🚀 STREAMING CHAT ENDPOINT STARTED: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate streaming response chunks"""
        try:
            # Step 1: Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Processing your request...', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Step 2: Session management
            step2_start = time.time()
            print(f"   📋 Step 2: Session management...")
            
            session = await get_session(request.session_id)
            if not session:
                try:
                    session = await create_session(
                        session_id=request.session_id,
                        user_id=current_user["id"]
                    )
                    if not session:
                        raise HTTPException(status_code=500, detail="Failed to create session")
                    logger.info(f"Created new session: {request.session_id}")
                except Exception as e:
                    logger.error(f"Failed to create session: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'message': f'Failed to create session: {str(e)}'})}\n\n"
                    return
            
            step2_time = time.time() - step2_start
            print(f"   ✅ Step 2 completed in {step2_time:.3f}s (Session management)")
            
            # Step 3: Send session ready status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Session ready, analyzing your message...', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Step 4: Process message with CrewAI (this is the main bottleneck)
            step4_start = time.time()
            print(f"   🤖 Step 4: Processing with OpenAI...")
            
            # Send processing status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Generating response...', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Use the new OpenAI function setup
            response = await money_mentor_function.process_message(
                message=request.query,
                chat_history=session.get("chat_history", []),
                session_id=request.session_id
            )
            
            step4_time = time.time() - step4_start
            print(f"   ✅ Step 4 completed in {step4_time:.3f}s (OpenAI processing)")
            
            # Step 5: Send the complete response
            yield f"data: {json.dumps({'type': 'response', 'data': response, 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Step 6: Background tasks (non-blocking)
            step6_start = time.time()
            print(f"   🔄 Step 6: Background tasks...")
            
            # Add user message to history (non-blocking)
            user_message = {
                "role": "user",
                "content": request.query,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add assistant response to history (non-blocking)
            assistant_message = {
                "role": "assistant", 
                "content": response.get("message", ""),
                "timestamp": datetime.now().isoformat()
            }
            
            # Run background tasks asynchronously
            asyncio.create_task(add_chat_message(request.session_id, user_message))
            asyncio.create_task(add_chat_message(request.session_id, assistant_message))
            
            step6_time = time.time() - step6_start
            print(f"   ✅ Step 6 completed in {step6_time:.3f}s (Background tasks)")
            
            # Step 7: Send completion status
            total_time = time.time() - start_time
            yield f"data: {json.dumps({'type': 'complete', 'message': 'Response complete', 'total_time': total_time, 'timestamp': datetime.now().isoformat()})}\n\n"
            
            print(f"🏁 STREAMING CHAT ENDPOINT COMPLETED in {total_time:.3f}s")
            print(f"   📊 Breakdown:")
            print(f"      - Session management: {step2_time:.3f}s ({(step2_time/total_time)*100:.1f}%)")
            print(f"      - OpenAI processing: {step4_time:.3f}s ({(step4_time/total_time)*100:.1f}%)")
            print(f"      - Background tasks: {step6_time:.3f}s ({(step6_time/total_time)*100:.1f}%)")
            
        except Exception as e:
            total_time = time.time() - start_time
            print(f"❌ STREAMING CHAT ENDPOINT FAILED after {total_time:.3f}s: {e}")
            logger.error(f"Failed to process streaming message: {e}")
            
            error_response = {
                "type": "error",
                "message": "I apologize, but I encountered an error processing your request. Please try again.",
                "session_id": request.session_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            yield f"data: {json.dumps(error_response)}\n\n"
        
        finally:
            # Always send stream end marker
            yield f"data: {json.dumps({'type': 'stream_end', 'timestamp': datetime.now().isoformat()})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*"
        }
    )

@router.post("/stream/simple")
async def process_message_streaming_simple(
    request: ChatMessageRequest,
    current_user: dict = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Simplified streaming endpoint that shows the basic StreamingResponse pattern.
    This is the minimal implementation of Option A.
    """
    async def generate_simple_stream() -> AsyncGenerator[str, None]:
        try:
            # Send initial status
            yield f"data: {json.dumps({'type': 'start', 'message': 'Starting to process your request...'})}\n\n"
            
            # Process the message using existing services
            response = await chat_service.process_message(
                query=request.query,
                session_id=request.session_id
            )
            
            # Send the complete response
            yield f"data: {json.dumps({'type': 'response', 'data': response})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        finally:
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
    
    return StreamingResponse(
        generate_simple_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@router.post("/stream/progressive")
async def process_message_streaming_progressive(
    request: ChatMessageRequest,
    current_user: dict = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Progressive streaming endpoint that shows how to stream partial responses.
    This demonstrates a more advanced streaming pattern.
    """
    async def generate_progressive_stream() -> AsyncGenerator[str, None]:
        try:
            # Step 1: Initial acknowledgment
            yield f"data: {json.dumps({'type': 'status', 'step': 1, 'message': 'Received your message'})}\n\n"
            await asyncio.sleep(0.1)  # Small delay for demonstration
            
            # Step 2: Session check
            yield f"data: {json.dumps({'type': 'status', 'step': 2, 'message': 'Checking session...'})}\n\n"
            session = await get_session(request.session_id)
            if not session:
                session = await create_session(
                    session_id=request.session_id,
                    user_id=current_user["id"]
                )
            await asyncio.sleep(0.1)
            
            # Step 3: Analysis
            yield f"data: {json.dumps({'type': 'status', 'step': 3, 'message': 'Analyzing your request...'})}\n\n"
            await asyncio.sleep(0.2)
            
            # Step 4: Processing
            yield f"data: {json.dumps({'type': 'status', 'step': 4, 'message': 'Generating response...'})}\n\n"
            
            # Use new OpenAI function
            response = await money_mentor_function.process_message(
                message=request.query,
                chat_history=session.get("chat_history", []),
                session_id=request.session_id
            )
            
            # Step 5: Send response in chunks (simulate progressive loading)
            message = response.get("message", "")
            words = message.split()
            chunk_size = max(1, len(words) // 4)  # Split into ~4 chunks
            
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size])
                yield f"data: {json.dumps({'type': 'partial', 'chunk': chunk, 'progress': min(100, (i + chunk_size) * 100 // len(words))})}\n\n"
                await asyncio.sleep(0.1)  # Small delay between chunks
            
            # Step 6: Complete response
            yield f"data: {json.dumps({'type': 'complete', 'data': response})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        finally:
            yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"
    
    return StreamingResponse(
        generate_progressive_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@router.get("/stream/health")
async def streaming_health_check():
    """Health check endpoint for streaming functionality"""
    return {
        "status": "healthy",
        "streaming": True,
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/api/streaming/stream",
            "/api/streaming/stream/simple", 
            "/api/streaming/stream/progressive"
        ]
    } 