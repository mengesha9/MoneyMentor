from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging
import json
import asyncio
from datetime import datetime

from app.models.schemas import (
    CourseStartRequest, CourseStartResponse,
    CourseNavigateRequest, CourseNavigateResponse,
    CourseQuizSubmitRequest, CourseQuizSubmitResponse,
    CourseCompleteRequest, CourseCompleteResponse
)
from app.services.course_service import CourseService
from app.services.background_sync_service import background_sync_service
from app.core.database import get_supabase

router = APIRouter()
logger = logging.getLogger(__name__)

def get_course_service() -> CourseService:
    """Get CourseService instance"""
    return CourseService()

@router.post("/start", response_model=CourseStartResponse)
async def start_course(
    request: CourseStartRequest,
    course_service: CourseService = Depends(get_course_service)
) -> Dict[str, Any]:
    """Start a course for a user"""
    try:
        result = await course_service.start_course(
            user_id=request.user_id,
            course_id=request.course_id
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start course: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start course: {str(e)}")

@router.post("/navigate", response_model=CourseNavigateResponse)
async def navigate_course_page(
    request: CourseNavigateRequest,
    course_service: CourseService = Depends(get_course_service)
) -> Dict[str, Any]:
    """Navigate to a specific page in a course"""
    try:
        result = await course_service.navigate_course_page(
            user_id=request.user_id,
            course_id=request.course_id,
            page_index=request.page_index
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to navigate course page: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to navigate course page: {str(e)}")

@router.post("/quiz/submit", response_model=CourseQuizSubmitResponse)
async def submit_course_quiz(
    request: CourseQuizSubmitRequest,
    course_service: CourseService = Depends(get_course_service)
) -> Dict[str, Any]:
    """Submit a quiz answer for a course page"""
    try:
        result = await course_service.submit_course_quiz(
            user_id=request.user_id,
            course_id=request.course_id,
            page_index=request.page_index,
            selected_option=request.selected_option,
            correct=request.correct
        )
        
        # Trigger background sync to Google Sheets after successful quiz submission (non-blocking)
        try:
            # Use the existing background sync service asynchronously
            asyncio.create_task(background_sync_service.force_sync_now())
            logger.info(f"Background sync triggered for user {request.user_id} after course quiz submission")
            
        except Exception as e:
            logger.warning(f"Failed to trigger background sync after course quiz submission: {e}")
            # Don't fail the entire request if sync fails
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to submit course quiz: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit course quiz: {str(e)}")

@router.post("/complete", response_model=CourseCompleteResponse)
async def complete_course(
    request: CourseCompleteRequest,
    course_service: CourseService = Depends(get_course_service)
) -> Dict[str, Any]:
    """Complete a course for a user"""
    try:
        result = await course_service.complete_course(
            user_id=request.user_id,
            course_id=request.course_id
        )
        
        # Trigger background sync to Google Sheets after course completion (non-blocking)
        try:
            # Use the existing background sync service asynchronously
            asyncio.create_task(background_sync_service.force_sync_now())
            logger.info(f"Background sync triggered for user {request.user_id} after course completion")
            
        except Exception as e:
            logger.warning(f"Failed to trigger background sync after course completion: {e}")
            # Don't fail the entire request if sync fails
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to complete course: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to complete course: {str(e)}")

@router.get("/{course_id}")
async def get_course_details(course_id: str):
    """Get course details by ID - database only"""
    try:
        supabase = get_supabase()
        
        # Get course from database only
        result = supabase.table('courses').select('*').eq('id', course_id).execute()
        
        if not result.data:
            logger.error(f"Course {course_id} not found in database")
            raise HTTPException(status_code=404, detail=f"Course not found: {course_id}")
        
        course_data = result.data[0]
        
        # Parse JSON fields that were stored as strings
        json_fields = ['learning_objectives', 'core_concepts', 'key_terms', 'real_life_scenarios', 'mistakes_to_avoid', 'action_steps']
        for field in json_fields:
            if field in course_data and isinstance(course_data[field], str):
                try:
                    course_data[field] = json.loads(course_data[field])
                except Exception as parse_error:
                    logger.warning(f"Failed to parse {field} for course {course_id}: {parse_error}")
                    course_data[field] = []
        
        return {
            "success": True,
            "data": course_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get course details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get course details: {str(e)}")

@router.get("/{course_id}/pages")
async def get_course_pages(course_id: str):
    """Get all pages for a course"""
    try:
        supabase = get_supabase()
        result = supabase.table('course_pages').select('*').eq('course_id', course_id).order('page_index').execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Course pages not found")
        
        return {
            "success": True,
            "data": result.data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get course pages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get course pages: {str(e)}")

@router.get("/user/{user_id}/sessions")
async def get_user_course_sessions(user_id: str):
    """Get all course sessions for a user"""
    try:
        supabase = get_supabase()
        result = supabase.table('user_course_sessions').select('*').eq('user_id', user_id).execute()
        
        return {
            "success": True,
            "data": result.data
        }
        
    except Exception as e:
        logger.error(f"Failed to get user course sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user course sessions: {str(e)}") 