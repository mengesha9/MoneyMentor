import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.routes import chat, quiz, calculation, progress, content, course, streaming_chat, user, session, sync, admin
from app.services.background_sync_service import background_sync_service
from app.services.database_listener_service import database_listener_service
from app.services.session_cleanup_service import session_cleanup_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events"""
    logger.info("🚀 Starting MoneyMentor API...")

    # Startup: Initialize background services
    try:
        logger.info("🔄 Starting background sync service...")
        await background_sync_service.start_background_sync()
        logger.info("✅ Background sync service started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to start background sync service: {e}")

    try:
        logger.info("🔄 Starting database listener service...")
        await database_listener_service.start_listener()
        logger.info("✅ Database listener service started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to start database listener service: {e}")

    try:
        logger.info("🔄 Starting session cleanup service...")
        await session_cleanup_service.start_cleanup_service()
        logger.info("✅ Session cleanup service started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to start session cleanup service: {e}")

    logger.info("🎉 All background services started successfully")

    yield

    # Shutdown: Clean up background services
    logger.info("🛑 Shutting down MoneyMentor API...")

    try:
        logger.info("🛑 Stopping background sync service...")
        await background_sync_service.stop_background_sync()
        logger.info("✅ Background sync service stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping background sync service: {e}")

    try:
        logger.info("🛑 Stopping database listener service...")
        await database_listener_service.stop_listener()
        logger.info("✅ Database listener service stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping database listener service: {e}")

    try:
        logger.info("🛑 Stopping session cleanup service...")
        await session_cleanup_service.stop_cleanup_service()
        logger.info("✅ Session cleanup service stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping session cleanup service: {e}")

    logger.info("👋 MoneyMentor API shutdown complete")


port = int(os.environ.get("PORT", 8080))
# Log the allowed origins
print("✅ Allowed CORS origins:", settings.CORS_ORIGINS)
app = FastAPI(
    title="MoneyMentor API",
    description="AI-powered financial education chatbot with quiz engine and calculation services",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request priority middleware (pauses background sync during user requests)
from app.middleware.request_priority import RequestPriorityMiddleware
app.add_middleware(RequestPriorityMiddleware)

# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed information"""
    
    # 🔍 ENHANCED VALIDATION ERROR REPORTING
    print("=" * 80)
    print("❌ FASTAPI VALIDATION ERROR DETAILS")
    print("=" * 80)
    print(f"🚨 Endpoint: {request.method} {request.url}")
    print(f"🚨 Error Type: RequestValidationError")
    print(f"🚨 Number of Errors: {len(exc.errors())}")
    
    # Show each validation error
    for i, error in enumerate(exc.errors()):
        print(f"\n🔍 Validation Error {i+1}:")
        print(f"  📍 Location: {' -> '.join(str(loc) for loc in error['loc'])}")
        print(f"  🚨 Error Type: {error['type']}")
        print(f"  💬 Message: {error['msg']}")
        print(f"  📊 Input: {error.get('input', 'NOT_PROVIDED')}")
    
    # Show the raw request body if available
    try:
        body = await request.body()
        if body:
            print(f"\n📝 Raw Request Body: {body.decode()}")
    except:
        print("\n📝 Raw Request Body: Could not read")
    
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
    
    print("🔍 VALIDATION RULES:")
    print("  • user_id: Must be a valid UUID string")
    print("  • quiz_type: Must be exactly 'diagnostic' or 'micro'")
    print("  • session_id: Must be a valid UUID string")
    print("  • responses: Must be an array of response objects")
    print("  • selected_option: Must be exactly 'A', 'B', 'C', or 'D'")
    print("  • correct: Must be true or false (boolean)")
    print("  • topic: Must be a non-empty string")
    print("=" * 80)
    
    # Return detailed error response
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "Request data format is invalid",
            "validation_errors": [
                {
                    "location": " -> ".join(str(loc) for loc in error['loc']),
                    "type": error['type'],
                    "message": error['msg'],
                    "input": error.get('input', 'NOT_PROVIDED')
                }
                for error in exc.errors()
            ],
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
            "endpoint": f"{request.method} {request.url}",
            "help": "Check the validation_errors array for specific field issues"
        }
    )

# General exception handler for other errors
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with detailed information"""
    
    print("=" * 80)
    print("❌ GENERAL EXCEPTION ERROR DETAILS")
    print("=" * 80)
    print(f"🚨 Endpoint: {request.method} {request.url}")
    print(f"🚨 Error Type: {type(exc).__name__}")
    print(f"🚨 Error Message: {str(exc)}")
    
    # Show the raw request body if available
    try:
        body = await request.body()
        if body:
            print(f"\n📝 Raw Request Body: {body.decode()}")
    except:
        print("\n📝 Raw Request Body: Could not read")
    
    print("=" * 80)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "error_type": type(exc).__name__,
            "error_details": str(exc),
            "endpoint": f"{request.method} {request.url}",
            "help": "Check server logs for more details"
        }
    )

# Include API routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["quiz"])
app.include_router(calculation.router, prefix="/api/calculation", tags=["calculation"])
app.include_router(progress.router, prefix="/api/progress", tags=["progress"])
app.include_router(content.router, prefix="/api", tags=["Content Management"])
app.include_router(course.router, prefix="/api/course", tags=["course"])
app.include_router(streaming_chat.router, prefix="/api/streaming", tags=["streaming"])
app.include_router(user.router, prefix="/api/user", tags=["user"])
app.include_router(session.router, prefix="/api/session", tags=["session"])
app.include_router(sync.router, prefix="/api/sync", tags=["sync"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

# Background services are now triggered on-demand after quiz submissions
# This prevents API blocking and ensures Google Sheets sync happens when needed

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "MoneyMentor API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint - optimized for speed"""
    import time
    return {
        "status": "healthy", 
        "service": "MoneyMentor API",
        "timestamp": time.time(),
        "message": "API is running and ready"
    }

@app.get("/sync/status")
async def get_sync_status():
    """Get background sync service status"""
    return background_sync_service.get_sync_status()

@app.get("/sync/supabase-listener")
async def get_supabase_listener_status():
    """Get Supabase real-time listener service status"""
    from app.services.supabase_listener_service import supabase_listener_service
    return supabase_listener_service.get_status()

@app.post("/sync/force")
async def force_sync():
    """Force an immediate sync to Google Sheets"""
    success = await background_sync_service.force_sync_now()
    return {
        "success": success,
        "message": "Sync completed" if success else "Sync failed"
    }

@app.get("/session/cleanup/status")
async def get_session_cleanup_status():
    """Get session cleanup service status"""
    return session_cleanup_service.get_status()

@app.post("/session/cleanup/force")
async def force_session_cleanup():
    """Force an immediate session cleanup"""
    result = await session_cleanup_service.force_cleanup_now()
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
        log_level="info"
    ) 
