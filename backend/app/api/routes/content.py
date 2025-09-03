from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import Dict, Any, Optional, List
import logging

from app.services.content_service import ContentService
from app.models.schemas import ContentDocument, SearchRequest

logger = logging.getLogger(__name__)
router = APIRouter()

def get_content_service() -> ContentService:
    """Get ContentService instance"""
    return ContentService()

# Content management endpoints - specific paths first
@router.delete("/chunks/clear-all",
    summary="Clear all content",
    description="Delete all content chunks and reset file statuses"
)
async def clear_all_content(
    content_service: ContentService = Depends(get_content_service)
) -> Dict[str, Any]:
    """Clear all content chunks and reset file statuses"""
    success = await content_service.delete_content_chunks("clear-all")
    if not success:
        raise HTTPException(status_code=500, detail="Failed to clear all content")
    return {"status": "success", "message": "All content chunks cleared successfully"}

@router.get("/chunks/storage",
    summary="Get storage usage",
    description="Get statistics about content storage usage including total chunks and size"
)
async def get_storage_usage(
    content_service: ContentService = Depends(get_content_service)
) -> Dict[str, Any]:
    """Get storage usage statistics"""
    return await content_service.get_storage_usage()

@router.post("/chunks/cleanup",
    summary="Clean up old content",
    description="Delete content chunks older than specified number of days"
)
async def cleanup_content(
    days: int = 7,
    content_service: ContentService = Depends(get_content_service)
) -> Dict[str, Any]:
    """Clean up content older than specified days"""
    return await content_service.cleanup_old_content(days)

@router.post("/chunks/optimize",
    summary="Optimize storage",
    description="Remove duplicate chunks and optimize storage usage"
)
async def optimize_storage(
    content_service: ContentService = Depends(get_content_service)
) -> Dict[str, Any]:
    """Optimize storage by removing duplicates"""
    return await content_service.optimize_storage()

@router.delete("/chunks/{file_id}", 
    summary="Delete specific content",
    description="Delete all chunks associated with a specific file ID"
)
async def delete_content(
    file_id: str,
    content_service: ContentService = Depends(get_content_service)
) -> Dict[str, Any]:
    """Delete content chunks for a specific file"""
    success = await content_service.delete_content_chunks(file_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete content")
    return {"status": "success", "message": f"Content for file {file_id} deleted successfully"}

# Existing content endpoints
@router.post("/search")
async def search_content(request: SearchRequest):
    """Search for relevant content using vector similarity"""
    try:
        results = get_content_service().search_content(
            query=request.query,
            limit=request.limit,
            filter_metadata=request.filter_metadata
        )
        return {"results": results}
    except Exception as e:
        logger.error(f"Content search failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to search content")

@router.get("/performance")
async def get_search_performance():
    """Get vector search performance metrics"""
    try:
        metrics = get_content_service().get_search_performance_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")

@router.post("/ingest")
async def ingest_document(document: ContentDocument):
    """Ingest a new document into the vector store"""
    try:
        document_id = get_content_service().ingest_document(
            file_path=document.file_path,
            title=document.title,
            source_type=document.source_type
        )
        return {"document_id": document_id}
    except Exception as e:
        logger.error(f"Document ingestion failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to ingest document")

@router.post("/upload")
async def upload_content(file: UploadFile = File(...)):
    """Upload and process content for RAG"""
    try:
        content = await file.read()
        result = await get_content_service().process_content(
            content=content,
            filename=file.filename,
            content_type=file.content_type
        )
        return {
            "message": "Content processed successfully",
            "file_id": result["file_id"],
            "chunks": result["chunks"]
        }
    except Exception as e:
        logger.error(f"Content processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/batch")
async def upload_batch(files: List[UploadFile] = File(...)):
    """Upload and process multiple files for RAG"""
    try:
        results = []
        for file in files:
            content = await file.read()
            result = await get_content_service().process_content(
                content=content,
                filename=file.filename,
                content_type=file.content_type
            )
            results.append({
                "filename": file.filename,
                "file_id": result["file_id"],
                "chunks": result["chunks"]
            })
        return {
            "message": "Batch processing completed",
            "results": results
        }
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 