import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
import numpy as np
import asyncio
from functools import lru_cache

from app.core.database import supabase
from app.core.config import settings
from app.utils.user_validation import require_authenticated_user_id, sanitize_user_id_for_logging
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)

class HybridMemoryManager:
    """
    Hybrid Memory Manager: Smart Sliding Window + Vector DB
    - Recent messages: user_sessions table (fast DB query)
    - Older messages: vector_memory table (similarity search)
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
        self.sliding_window_size = 4  # Reduced from 6 to 4 for faster processing
        self.vector_search_limit = 5  # Reduced from 10 to 5 for faster retrieval
        self.similarity_threshold = 0.6  # Increased threshold for better precision
        self.max_tokens = 2000  # Reduced from 4000 to 2000 for faster processing
        
        # Embedding cache to reduce API calls
        self.embedding_cache = {}  # text -> embedding
        self.cache_size_limit = 1000
    
    @lru_cache(maxsize=100)
    def _get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding if available"""
        return self.embedding_cache.get(text)
    
    def _cache_embedding(self, text: str, embedding: List[float]):
        """Cache embedding with size limit"""
        if len(self.embedding_cache) >= self.cache_size_limit:
            # Remove oldest entries (simple FIFO)
            oldest_key = next(iter(self.embedding_cache))
            del self.embedding_cache[oldest_key]
        
        self.embedding_cache[text] = embedding
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for text using OpenAI with caching"""
        if not self.embeddings:
            return None
        
        # Check cache first
        cached = self._get_cached_embedding(text)
        if cached:
            return cached
        
        try:
            embedding = await self.embeddings.aembed_query(text)
            if embedding:
                self._cache_embedding(text, embedding)
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    async def add_to_memory(self, message: Dict[str, Any], user_id: str, session_id: str):
        """Add message to user_sessions ONLY (OPTIMIZED FOR SPEED)"""
        try:
            # Validate user_id is a real UUID from authentication
            validated_user_id = require_authenticated_user_id(user_id, "hybrid memory operation")
            sanitized_user_id = sanitize_user_id_for_logging(validated_user_id)
            
            content = message.get('content', '')
            role = message.get('role', '')
            timestamp = message.get('timestamp', datetime.now(timezone.utc).isoformat())
            
            # 1. Get current session and chat history
            session = await self._get_session(validated_user_id)
            if not session:
                logger.warning(f"Session for user {sanitized_user_id} not found - this is normal for new sessions")
                return
            
            # Get chat history from session_data JSONB field
            session_data = session.get("session_data", {})
            chat_history = session_data.get("chat_history", [])
            
            # 2. Add new message to chat history
            chat_history.append(message)
            
            # 3. OPTIMIZATION: Keep only recent 4 messages (no vector DB)
            # COMMENTED OUT: Vector DB operations (causing performance bottleneck)
            # moved_messages = []
            # if len(chat_history) > self.sliding_window_size:
            #     moved_messages = chat_history[:-self.sliding_window_size]
            #     chat_history = chat_history[-self.sliding_window_size:]
            
            # OPTIMIZED: Keep last 4 messages only
            if len(chat_history) > 4:
                chat_history = chat_history[-4:]  # Keep only last 4 messages
            
            # 4. Update user_sessions with new chat history (target specific session)
            await self._update_session(validated_user_id, {"chat_history": chat_history}, session_id)
            
            # 5. COMMENTED OUT: Vector DB storage (causing performance bottleneck)
            # if moved_messages:
            #     for old_message in moved_messages:
            #         await self._add_to_vector_db(old_message, user_id, session_id)
            #     logger.info(f"Moved {len(moved_messages)} messages to vector DB")
            
            logger.info(f"OPTIMIZED: Added message to user_sessions only (vector DB DISABLED)")
            
        except Exception as e:
            logger.error(f"Failed to add message to optimized memory: {e}")
    
    async def _get_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get session from user_sessions table by user_id"""
        try:
            # Validate user_id is a real UUID
            validated_user_id = require_authenticated_user_id(user_id, "session retrieval")
            sanitized_user_id = sanitize_user_id_for_logging(validated_user_id)
            
            # Find by user_id
            result = supabase.table("user_sessions").select("*").eq("user_id", validated_user_id).order("created_at", desc=True).limit(1).execute()
            if result.data:
                return result.data[0]
            
            return None
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None
    
    async def _update_session(self, user_id: str, data: Dict[str, Any], session_id: str = None):
        """Update session in user_sessions table by session_id (preferred) or user_id (fallback)"""
        try:
            # Validate user_id is a real UUID
            validated_user_id = require_authenticated_user_id(user_id, "session update")
            sanitized_user_id = sanitize_user_id_for_logging(validated_user_id)
            
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            # Prefer session_id if provided, otherwise fall back to user_id
            if session_id:
                # Update by session_id (targets specific session)
                result = supabase.table("user_sessions").update(data).eq("session_id", session_id).execute()
                if result.data:
                    logger.debug(f"Updated session {session_id} for user {sanitized_user_id}")
                    return
                else:
                    logger.warning(f"Session {session_id} not found, falling back to user_id update")
            
            # Fallback: Update by user_id (updates all sessions for user - NOT RECOMMENDED)
            result = supabase.table("user_sessions").update(data).eq("user_id", validated_user_id).execute()
            if result.data:
                logger.warning(f"Updated {len(result.data)} sessions for user {sanitized_user_id} (fallback mode)")
                return
            
            raise ValueError(f"Failed to update session for user {sanitized_user_id}")
        except Exception as e:
            logger.error(f"Failed to update session: {e}")
            raise
    
    async def _add_to_vector_db(self, message: Dict[str, Any], user_id: str, session_id: str):
        """Add message to vector database for long-term storage"""
        try:
            # Validate user_id is a real UUID
            validated_user_id = require_authenticated_user_id(user_id, "vector database storage")
            sanitized_user_id = sanitize_user_id_for_logging(validated_user_id)
            
            content = message.get('content', '')
            role = message.get('role', '')
            timestamp = message.get('timestamp', datetime.now(timezone.utc).isoformat())
            
            # Generate embedding (only when moving to vector DB)
            embedding = await self.get_embedding(content)
            if not embedding:
                logger.warning("Failed to generate embedding, skipping vector storage")
                return
            
            # Store in vector database
            memory_data = {
                'id': f"{session_id}_{timestamp}",
                'user_id': validated_user_id,
                'session_id': session_id,
                'content': content,
                'role': role,
                'timestamp': timestamp,
                'embedding': embedding,  # OpenAI returns list[float] which pgvector can handle
                'metadata': {
                    'message_type': 'chat',
                    'importance_score': self._calculate_importance(content, role)
                }
            }
            
            # Store in vector_memory table
            result = supabase.table('vector_memory').upsert(memory_data).execute()
            
            if result.data:
                logger.debug(f"Added message to vector DB: {len(embedding)} dimensions")
            else:
                logger.error("Failed to store message in vector DB")
                
        except Exception as e:
            logger.error(f"Failed to add message to vector DB: {e}")
    
    async def get_context_for_query(self, query: str, user_id: str, session_id: str) -> List[Dict[str, Any]]:
        """Get context using ONLY recent messages from user_sessions (OPTIMIZED FOR SPEED)"""
        try:
            # Validate user_id is a real UUID
            validated_user_id = require_authenticated_user_id(user_id, "context retrieval")
            sanitized_user_id = sanitize_user_id_for_logging(validated_user_id)
            
            # OPTIMIZATION: Skip vector similarity search for speed testing
            # Only use recent messages from user_sessions table
            
            # 1. Get recent messages from user_sessions (fast, synchronous)
            recent_messages = await self._get_sliding_window_messages(validated_user_id)
            
            # 2. COMMENTED OUT: Vector similarity search (causing 7.876s bottleneck)
            # similar_messages = []
            # if len(recent_messages) < self.sliding_window_size:
            #     similar_messages = await self._get_similar_messages(query, user_id)
            
            # 3. Use only recent messages (no vector search)
            all_messages = recent_messages  # No similar_messages added
            
            # 4. Remove duplicates and rank by relevance
            unique_messages = self._deduplicate_and_rank(all_messages, query)
            
            # 5. Limit by token count
            limited_messages = self._limit_by_tokens(unique_messages)
            
            logger.info(f"OPTIMIZED: Retrieved {len(limited_messages)} messages from user_sessions only (vector DB DISABLED)")
            return limited_messages
            
        except Exception as e:
            logger.error(f"Failed to get context for query: {e}")
            return []
    
    async def _get_sliding_window_messages(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recent messages from user_sessions table"""
        try:
            # Validate user_id is a real UUID
            validated_user_id = require_authenticated_user_id(user_id, "sliding window retrieval")
            
            session = await self._get_session(validated_user_id)
            if not session:
                return []
            
            # Get chat history from chat_history JSONB field
            chat_history = session.get("chat_history", [])
            
            messages = []
            for msg in chat_history:
                messages.append({
                    'content': msg.get('content', ''),
                    'role': msg.get('role', ''),
                    'timestamp': msg.get('timestamp', ''),
                    'similarity_score': 1.0,  # Recent messages get high score
                    'source': 'sliding_window'
                })
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get sliding window messages: {e}")
            return []
    
    async def _get_similar_messages(self, query: str, user_id: str) -> List[Dict[str, Any]]:
        """Get similar messages using vector similarity"""
        try:
            # Validate user_id is a real UUID
            validated_user_id = require_authenticated_user_id(user_id, "similar messages retrieval")
            
            # Get query embedding
            query_embedding = await self.get_embedding(query)
            if not query_embedding:
                return []
            
            # Get all user messages from vector DB
            result = supabase.table('vector_memory')\
                .select('*')\
                .eq('user_id', validated_user_id)\
                .execute()
            
            if not result.data:
                return []
            
            # Calculate similarities (optimized batch processing)
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
                            'source': 'vector_similarity'
                        })
            
            # Sort by similarity and take top results
            similar_messages.sort(key=lambda x: x['similarity_score'], reverse=True)
            return similar_messages[:self.vector_search_limit]
            
        except Exception as e:
            logger.error(f"Failed to get similar messages: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            # Convert vec1 to numpy array
            vec1 = np.array(vec1, dtype=float)
            
            # Handle vec2 which might be a string from database
            if isinstance(vec2, str):
                try:
                    vec2 = json.loads(vec2)
                except:
                    logger.error(f"Failed to parse embedding string: {vec2[:50]}...")
                    return 0.0
            
            vec2 = np.array(vec2, dtype=float)
            
            # Ensure both vectors have the same shape
            if vec1.shape != vec2.shape:
                logger.error(f"Vector shape mismatch: {vec1.shape} vs {vec2.shape}")
                return 0.0
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
            
        except Exception as e:
            logger.error(f"Failed to calculate cosine similarity: {e}")
            return 0.0
    
    def _deduplicate_and_rank(self, messages: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Remove duplicates and rank by relevance"""
        seen_contents = set()
        unique_messages = []
        
        for msg in messages:
            content_hash = hash(msg['content'])
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_messages.append(msg)
        
        # Sort by similarity score (sliding window messages already have high scores)
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
    
    def _calculate_importance(self, content: str, role: str) -> float:
        """Calculate importance score"""
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
    
    async def clear_session(self, user_id: str, session_id: str = None):
        """Clear chat history for a user (specific session if session_id provided)"""
        try:
            # Validate user_id is a real UUID
            validated_user_id = require_authenticated_user_id(user_id, "session clearing")
            sanitized_user_id = sanitize_user_id_for_logging(validated_user_id)
            
            await self._update_session(validated_user_id, {"chat_history": []}, session_id)
            if session_id:
                logger.info(f"Cleared chat history for session {session_id} of user {sanitized_user_id}")
            else:
                logger.info(f"Cleared chat history for all sessions of user {sanitized_user_id}")
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
    
    async def cleanup_old_messages(self, days_to_keep: int = 30):
        """Clean up old messages from vector database"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            
            result = supabase.table('vector_memory')\
                .delete()\
                .lt('timestamp', cutoff_date.isoformat())\
                .execute()
            
            logger.info(f"Cleaned up old vector memory messages")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old messages: {e}")
    
    async def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Get memory statistics"""
        try:
            # Validate user_id is a real UUID
            validated_user_id = require_authenticated_user_id(user_id, "memory stats retrieval")
            sanitized_user_id = sanitize_user_id_for_logging(validated_user_id)
            
            session = await self._get_session(validated_user_id)
            if not session:
                return {
                    'sliding_window_size': 0,
                    'sliding_window_limit': self.sliding_window_size,
                    'vector_search_limit': self.vector_search_limit,
                    'similarity_threshold': self.similarity_threshold,
                    'max_tokens': self.max_tokens,
                    'cache_size': len(self.embedding_cache)
                }
            
            chat_history = session.get("chat_history", [])
            sliding_window_size = len(chat_history)
            
            return {
                'sliding_window_size': sliding_window_size,
                'sliding_window_limit': self.sliding_window_size,
                'vector_search_limit': self.vector_search_limit,
                'similarity_threshold': self.similarity_threshold,
                'max_tokens': self.max_tokens,
                'cache_size': len(self.embedding_cache)
            }
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {}

# Global hybrid memory manager instance
hybrid_memory_manager = HybridMemoryManager() 