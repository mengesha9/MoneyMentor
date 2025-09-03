from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
import shutil
from datetime import datetime

from app.services.content_service import ContentService
from app.core.config import settings
from app.schemas.content import (
    DocumentMetadata,
    TopicCreate,
    TopicResponse,
    SearchResponse
)

router = APIRouter()
content_service = ContentService()

@router.post("/upload", response_model=DocumentMetadata)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    topic: Optional[str] = Form(None)
):
    """Upload and process a document"""
    try:
        # Create upload directory if it doesn't exist
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Save file temporarily
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file type from extension
        file_type = file.filename.split(".")[-1].lower()
        if file_type not in ["pdf", "pptx", "docx", "txt"]:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Prepare metadata
        metadata = {
            "title": title,
            "description": description,
            "topic": topic,
            "original_filename": file.filename,
            "uploaded_at": datetime.utcnow().isoformat()
        }
        
        # Process document
        success = await content_service.process_document(file_path, file_type, metadata)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to process document")
        
        # Get document metadata
        doc_metadata = await content_service.get_document_metadata(file_path)
        if not doc_metadata:
            raise HTTPException(status_code=500, detail="Failed to retrieve document metadata")
        
        return doc_metadata
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

@router.get("/search", response_model=List[SearchResponse])
async def search_content(
    query: str,
    limit: int = 5,
    topic: Optional[str] = None
):
    """Search for content using vector similarity"""
    try:
        results = await content_service.search_content(query, limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/topics", response_model=List[TopicResponse])
async def get_topics():
    """Get list of available topics"""
    try:
        topics = await content_service.get_topics()
        return topics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/topics", response_model=TopicResponse)
async def create_topic(topic: TopicCreate):
    """Create a new topic"""
    try:
        success = await content_service.add_topic(topic.topic, topic.description)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create topic")
        return topic
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/{file_path:path}")
async def delete_document(file_path: str):
    """Delete a document and its chunks"""
    try:
        success = await content_service.delete_document(file_path)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete document")
        return JSONResponse(content={"message": "Document deleted successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 