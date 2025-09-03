from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class DocumentMetadata(BaseModel):
    """Schema for document metadata"""
    file_path: str = Field(..., description="Path to the document file")
    file_type: str = Field(..., description="Type of the document (pdf, pptx, docx, txt)")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata about the document")
    total_chunks: int = Field(..., description="Total number of chunks the document was split into")
    processed_at: datetime = Field(..., description="When the document was processed")

class TopicCreate(BaseModel):
    """Schema for creating a new topic"""
    topic: str = Field(..., description="Name of the topic")
    description: str = Field(..., description="Description of the topic")

class TopicResponse(BaseModel):
    """Schema for topic response"""
    topic: str = Field(..., description="Name of the topic")
    description: str = Field(..., description="Description of the topic")
    created_at: datetime = Field(..., description="When the topic was created")

class SearchResponse(BaseModel):
    """Schema for search results"""
    content: str = Field(..., description="Content of the matching chunk")
    metadata: Dict[str, Any] = Field(..., description="Metadata associated with the chunk")
    similarity_score: float = Field(..., description="Similarity score with the query") 