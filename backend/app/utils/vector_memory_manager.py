import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
import json
import numpy as np
import asyncio

from app.core.database import supabase
from app.core.config import settings
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)

class VectorMemoryManager:
    """
    Standard vector-based memory manager using similarity search
    Based on established chatbot memory techniques
    """
    
    def __init__(self):
        # Initialize OpenAI embeddings (same as content_service)
        try:
            self.embeddings = OpenAIEmbeddings(
                model=settings.OPENAI_EMBEDDING_MODEL,
                api_key=settings.OPENAI_API_KEY,
                request_timeout=60
            )
            logger.info("OpenAI embeddings initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI embeddings: {e}")
            self.embeddings = None
        
        # Configuration
        self.max_context_messages = 10
        self.similarity_threshold = 0.7
        self.max_tokens = 4000
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for text using OpenAI"""
        if not self.embeddings:
            return None
        
        try:
            embedding = await self.embeddings.aembed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    async def add_to_memory(self, message: Dict[str, Any], user_id: str, session_id: str):
        """Add message to vector memory"""
        try:
            content = message.get('content', '')
            role = message.get('role', '')
            timestamp = message.get('timestamp', datetime.now(timezone.utc).isoformat())
            
            # Generate embedding
            embedding = await self.get_embedding(content)
            if not embedding:
                logger.warning("Failed to generate embedding, skipping memory storage")
                return
            
            # Store in database
            memory_data = {
                'id': f"{session_id}_{timestamp}",
                'user_id': user_id,
                'session_id': session_id,
                'content': content,
                'role': role,
                'timestamp': timestamp,
                'embedding': embedding,  # OpenAI returns list[float] which pgvector can handle
                'metadata': {
                    'message_type': 'chat',
                    'importance_score': self._calculate_simple_importance(content, role)
                }
            }
            
            # Store in vector_memory table
            result = supabase.table('vector_memory').upsert(memory_data).execute()
            
            if result.data:
                logger.info(f"Added message to vector memory: {len(embedding)} dimensions")
            else:
                logger.error("Failed to store message in vector memory")
                
        except Exception as e:
            logger.error(f"Failed to add message to vector memory: {e}")
    
    async def get_context_for_query(self, query: str, user_id: str, session_id: str) -> List[Dict[str, Any]]:
        """Get relevant context using vector similarity search"""
        try:
            # Get query embedding
            query_embedding = await self.get_embedding(query)
            if not query_embedding:
                logger.warning("Failed to generate query embedding, returning empty context")
                return []
            
            # Get recent messages first (sliding window approach)
            recent_messages = await self._get_recent_messages(user_id, session_id, limit=5)
            
            # Get similar messages using vector search
            similar_messages = await self._get_similar_messages(query_embedding, user_id, limit=10)
            
            # Combine and rank results
            all_messages = recent_messages + similar_messages
            
            # Remove duplicates and rank by relevance
            unique_messages = self._deduplicate_and_rank(all_messages, query_embedding)
            
            # Limit by token count
            context_messages = self._limit_by_tokens(unique_messages)
            
            logger.info(f"Retrieved {len(context_messages)} messages from vector memory")
            return context_messages
            
        except Exception as e:
            logger.error(f"Failed to get context from vector memory: {e}")
            return []
    
    async def _get_recent_messages(self, user_id: str, session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent messages (sliding window approach)"""
        try:
            result = supabase.table('vector_memory')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .execute()
            
            messages = []
            for row in result.data:
                messages.append({
                    'content': row['content'],
                    'role': row['role'],
                    'timestamp': row['timestamp'],
                    'similarity_score': 1.0,  # Recent messages get high score
                    'source': 'recent'
                })
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get recent messages: {e}")
            return []
    
    async def _get_similar_messages(self, query_embedding: List[float], user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get similar messages using vector similarity"""
        try:
            # Get all user messages
            result = supabase.table('vector_memory')\
                .select('*')\
                .eq('user_id', user_id)\
                .execute()
            
            if not result.data:
                return []
            
            # Calculate similarities
            similar_messages = []
            for row in result.data:
                if row.get('embedding'):
                    similarity = self._cosine_similarity(query_embedding, row['embedding'])
                    
                    if similarity > self.similarity_threshold:
                        similar_messages.append({
                            'content': row['content'],
                            'role': row['role'],
                            'timestamp': row['timestamp'],
                            'similarity_score': similarity,
                            'source': 'similarity'
                        })
            
            # Sort by similarity and take top results
            similar_messages.sort(key=lambda x: x['similarity_score'], reverse=True)
            return similar_messages[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get similar messages: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception as e:
            logger.error(f"Failed to calculate cosine similarity: {e}")
            return 0.0
    
    def _deduplicate_and_rank(self, messages: List[Dict[str, Any]], query_embedding: List[float]) -> List[Dict[str, Any]]:
        """Remove duplicates and rank by relevance"""
        seen_contents = set()
        unique_messages = []
        
        for msg in messages:
            content_hash = hash(msg['content'])
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_messages.append(msg)
        
        # Sort by similarity score (recent messages already have high scores)
        unique_messages.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return unique_messages
    
    def _limit_by_tokens(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Limit context by estimated token count"""
        current_tokens = 0
        limited_messages = []
        
        for msg in messages:
            # Rough token estimation (words * 1.3)
            estimated_tokens = len(msg['content'].split()) * 1.3
            
            if current_tokens + estimated_tokens <= self.max_tokens:
                limited_messages.append(msg)
                current_tokens += estimated_tokens
            else:
                break
        
        return limited_messages
    
    def _calculate_simple_importance(self, content: str, role: str) -> float:
        """Calculate simple importance score"""
        score = 0.0
        
        # Role-based scoring
        if role == 'user':
            score += 0.3
        elif role == 'assistant':
            score += 0.2
        
        # Content-based scoring
        if '?' in content:
            score += 0.2
        
        if any(word in content.lower() for word in ['important', 'critical', 'urgent']):
            score += 0.3
        
        # Financial terms
        financial_terms = ['investment', 'savings', 'debt', 'retirement', '401k', 'portfolio']
        if any(term in content.lower() for term in financial_terms):
            score += 0.2
        
        return min(score, 1.0)
    
    async def cleanup_old_messages(self, days_to_keep: int = 30):
        """Clean up old messages"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            
            result = supabase.table('vector_memory')\
                .delete()\
                .lt('timestamp', cutoff_date.isoformat())\
                .execute()
            
            logger.info(f"Cleaned up old vector memory messages")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old messages: {e}")

# Global vector memory manager instance
vector_memory_manager = VectorMemoryManager() 