"""
Middleware to prioritize user requests over background tasks
"""
import time
import asyncio
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.background_sync_service import background_sync_service
from app.services.session_cleanup_service import session_cleanup_service
import logging

logger = logging.getLogger(__name__)

class RequestPriorityMiddleware(BaseHTTPMiddleware):
    """Middleware to pause background services during user requests"""
    
    def __init__(self, app):
        super().__init__(app)
        self.active_requests = 0
    
    async def dispatch(self, request: Request, call_next):
        # Increment active request counter
        self.active_requests += 1
        
        # Pause background services if this is the first active request
        if self.active_requests == 1:
            background_sync_service.pause_for_requests()
        
        try:
            # Process the request
            start_time = time.time()
            response = await call_next(request)
            request_time = time.time() - start_time
            
            # Log slow requests
            if request_time > 1.0:  # More than 1 second
                logger.warning(f"Slow request: {request.method} {request.url.path} took {request_time:.2f}s")
            
            return response
            
        finally:
            # Decrement active request counter
            self.active_requests -= 1
            
            # Resume background services if no more active requests
            if self.active_requests == 0:
                background_sync_service.resume_after_requests()