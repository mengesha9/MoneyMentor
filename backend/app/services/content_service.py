from typing import List, Dict, Any, Optional
import os
import logging
from datetime import datetime, timedelta
import uuid
import time
import PyPDF2
import docx2txt
import tempfile
import asyncio
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

from app.core.config import settings
from app.core.database import get_supabase

logger = logging.getLogger(__name__)

class ContentService:
    """Service for managing course content and vector search"""
    
    def __init__(self):
        self.supabase = get_supabase()
        self.embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY,
            request_timeout=60
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,  # Increased chunk size to reduce total chunks
            chunk_overlap=100,  # Reduced overlap
            length_function=len,
        )
        self.executor = ThreadPoolExecutor(max_workers=8)  # Increased workers
        self.session = None
        self.semaphore = asyncio.Semaphore(15)  # Increased concurrent API calls
        self.rate_limit_delay = 0.1  # 100ms delay between API calls
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def _process_single_chunk(self, file_id: str, chunk: str, chunk_index: int):
        """Process a single chunk with retry logic"""
        try:
            # Truncate chunk if it's too long
            max_chunk_length = 4000
            if len(chunk) > max_chunk_length:
                chunk = chunk[:max_chunk_length]
                logger.warning(f"Chunk {chunk_index} truncated to {max_chunk_length} characters")

            # Generate embedding with timeout
            embedding = await asyncio.wait_for(
                self.embeddings.aembed_query(chunk),
                timeout=60
            )
            
            # Store chunk with embedding - pgvector expects a list/array, not a string
            chunk_data = {
                'file_id': file_id,
                'chunk_index': chunk_index,
                'content': chunk,
                'embedding': embedding  # Keep as list/array for pgvector
            }
            
            # Direct insert without transaction
            self.supabase.table('content_chunks').insert(chunk_data).execute()
            
        except asyncio.TimeoutError:
            logger.warning(f"Timeout processing chunk {chunk_index}, retrying with exponential backoff...")
            raise
        except Exception as e:
            logger.error(f"Failed to process chunk {chunk_index}: {e}")
            raise
    
    async def _process_chunk_batch(self, file_id: str, chunks: List[str], start_index: int):
        """Process a batch of chunks concurrently with rate limiting"""
        tasks = []
        for i, chunk in enumerate(chunks):
            chunk_index = start_index + i
            # Add rate limiting delay between tasks
            if i > 0:
                await asyncio.sleep(self.rate_limit_delay)
            task = asyncio.create_task(
                self._process_single_chunk_with_semaphore(file_id, chunk, chunk_index)
            )
            tasks.append(task)
        
        # Wait for all tasks in the batch to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing chunk {start_index + i}: {str(result)}")
                raise result

    async def _process_single_chunk_with_semaphore(self, file_id: str, chunk: str, chunk_index: int):
        """Process a single chunk with semaphore for rate limiting"""
        async with self.semaphore:
            return await self._process_single_chunk(file_id, chunk, chunk_index)

    async def process_content(self, content: bytes, filename: str, content_type: str) -> Dict[str, Any]:
        """Process uploaded content and store in vector database"""
        try:
            file_id = str(uuid.uuid4())
            start_time = time.time()
            
            print(f"\n📄 Starting to process file: {filename}")
            print(f"📊 File size: {len(content) / 1024:.2f} KB")
            
            # Store file metadata
            file_metadata = {
                'file_id': file_id,
                'filename': filename,
                'content_type': content_type,
                'uploaded_at': datetime.utcnow().isoformat(),
                'status': 'processing',
                'chunk_count': 0,
                'processed_chunks': 0,
                'file_size': len(content),
                'retry_count': 0
            }
            
            # Store in Supabase
            result = self.supabase.table('content_files').insert(file_metadata).execute()
            print("✅ File metadata stored in database")
            
            # Process content based on type
            print(f"\n🔄 Processing {content_type} content...")
            if content_type.startswith('text/'):
                text_content = content.decode('utf-8')
            elif content_type == 'application/pdf':
                text_content = await self._process_pdf_async(content)
            elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                text_content = await self._process_docx_async(content)
            else:
                raise ValueError(f"Unsupported content type: {content_type}")
            
            # Split text into chunks
            print("\n✂️  Splitting content into chunks...")
            chunks = self.text_splitter.split_text(text_content)
            total_chunks = len(chunks)
            print(f"📑 Total chunks created: {total_chunks}")
            
            # Update total chunk count
            self.supabase.table('content_files').update({
                'chunk_count': total_chunks,
                'status': 'processing_chunks'
            }).eq('file_id', file_id).execute()
            
            # Process chunks in larger batches for better throughput
            batch_size = 30  # Increased batch size
            processed_chunks = 0
            failed_chunks = []
            
            print("\n🚀 Starting chunk processing...")
            print("=" * 50)
            
            # Create a progress bar
            from tqdm.asyncio import tqdm
            pbar = tqdm(total=total_chunks, desc="Processing chunks")
            
            for i in range(0, total_chunks, batch_size):
                batch = chunks[i:i + batch_size]
                try:
                    print(f"\n📦 Processing batch {i//batch_size + 1}/{(total_chunks + batch_size - 1)//batch_size}")
                    print(f"   Chunks {i} to {min(i + batch_size, total_chunks)}")
                    
                    await self._process_chunk_batch(file_id, batch, i)
                    processed_chunks += len(batch)
                    pbar.update(len(batch))
                    
                    # Calculate progress and estimated time remaining
                    progress = (processed_chunks / total_chunks) * 100
                    elapsed_time = time.time() - start_time
                    if processed_chunks > 0:
                        time_per_chunk = elapsed_time / processed_chunks
                        remaining_chunks = total_chunks - processed_chunks
                        estimated_time_remaining = time_per_chunk * remaining_chunks
                    else:
                        estimated_time_remaining = 0
                    
                    # Print progress
                    print(f"   ✅ Progress: {progress:.1f}%")
                    print(f"   ⏱️  Elapsed time: {elapsed_time:.1f}s")
                    print(f"   ⏳ Estimated time remaining: {estimated_time_remaining:.1f}s")
                    print(f"   📊 Processed: {processed_chunks}/{total_chunks} chunks")
                    
                    # Update progress with timing information
                    self.supabase.table('content_files').update({
                        'processed_chunks': processed_chunks,
                        'status': 'processing_chunks',
                        'progress_percentage': round(progress, 2),
                        'estimated_time_remaining': round(estimated_time_remaining, 2),
                        'failed_chunks': failed_chunks
                    }).eq('file_id', file_id).execute()
                    
                except Exception as e:
                    logger.error(f"Error processing batch {i}-{i+len(batch)}: {e}")
                    print(f"   ❌ Error in batch: {str(e)}")
                    failed_chunks.extend(range(i, i + len(batch)))
                    continue
            
            pbar.close()
            
            # Update final status
            total_time = time.time() - start_time
            final_status = 'processed' if not failed_chunks else 'partially_processed'
            
            print("\n" + "=" * 50)
            print(f"\n🏁 Processing complete!")
            print(f"📊 Final status: {final_status}")
            print(f"⏱️  Total processing time: {total_time:.1f}s")
            print(f"✅ Successfully processed: {processed_chunks}/{total_chunks} chunks")
            if failed_chunks:
                print(f"❌ Failed chunks: {len(failed_chunks)}")
            
            self.supabase.table('content_files').update({
                'status': final_status,
                'processed_chunks': processed_chunks,
                'progress_percentage': 100,
                'processing_time': round(total_time, 2),
                'failed_chunks': failed_chunks
            }).eq('file_id', file_id).execute()
            
            return {
                'file_id': file_id,
                'chunks': total_chunks,
                'processed_chunks': processed_chunks,
                'failed_chunks': failed_chunks,
                'status': final_status,
                'processing_time': round(total_time, 2)
            }
            
        except Exception as e:
            logger.error(f"Content processing failed: {e}")
            print(f"\n❌ Processing failed: {str(e)}")
            if 'file_id' in locals():
                self.supabase.table('content_files').update({
                    'status': 'failed',
                    'error': str(e)
                }).eq('file_id', file_id).execute()
            raise

    async def _process_docx_async(self, content: bytes) -> str:
        """Process DOCX content asynchronously"""
        try:
            # Create a temporary file for docx processing
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                # Process DOCX in a thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                text_content = await loop.run_in_executor(
                    self.executor,
                    self._extract_docx_text,
                    temp_file_path
                )
                return text_content
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"DOCX processing failed: {e}")
            raise

    async def _process_pdf_async(self, content: bytes) -> str:
        """Process PDF content asynchronously"""
        try:
            # Create a temporary file for PDF processing
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                # Process PDF in a thread pool
                loop = asyncio.get_event_loop()
                text_content = await loop.run_in_executor(
                    self.executor,
                    self._extract_pdf_text,
                    temp_file_path
                )
                return text_content
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            raise

    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            raise

    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from Word document"""
        try:
            return docx2txt.process(file_path)
        except Exception as e:
            logger.error(f"Word document text extraction failed: {e}")
            raise
    
    async def search_content(self, query: str, limit: Optional[int] = 5, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Search content using vector similarity search with caching for optimal performance"""
        start_time = time.time()
        try:
            if not query or not isinstance(query, str):
                logger.warning("Invalid query parameter provided")
                return []
            
            # Validate and normalize parameters
            try:
                limit = int(limit) if limit is not None else 5
                limit = max(1, min(limit, 20))  # Ensure limit is between 1 and 20
            except (ValueError, TypeError):
                limit = 5
                
            try:
                threshold = float(threshold)
                threshold = max(0.1, min(threshold, 1.0))  # Ensure threshold is between 0.1 and 1.0
            except (ValueError, TypeError):
                threshold = 0.7
            
            # OPTIMIZATION: Use a more aggressive threshold for faster results
            # For chat context, we want quick, relevant results rather than perfect matches
            optimized_threshold = max(0.15, threshold - 0.1)  # Lower threshold for speed
            
            # OPTIMIZATION: Reduce limit for faster retrieval in chat context
            optimized_limit = min(limit, 2)  # Max 2 results for chat context
            
            # Generate query embedding with optimized timeout
            query_embedding = await asyncio.wait_for(
                self.embeddings.aembed_query(query),
                timeout=3  # Reduced timeout for faster response
            )
            
            # Execute vector search using the match_chunks RPC function with optimized parameters
            result = self.supabase.rpc('match_chunks', {
                'query_embedding': query_embedding,
                'match_threshold': optimized_threshold,
                'match_count': optimized_limit
            }).execute()
            
            if result.data:
                # Process and validate results
                processed_results = []
                for item in result.data:
                    if isinstance(item, dict) and 'content' in item:
                        similarity = float(item.get('similarity', 0.0))
                        # Only include results above threshold
                        if similarity >= optimized_threshold:
                            # OPTIMIZATION: Truncate content for faster processing
                            content = item['content']
                            if len(content) > 300:  # Limit content length
                                content = content[:300] + "..."
                            
                            processed_results.append({
                                'content': content,
                                'metadata': {
                                    'file_id': item.get('file_id'),
                                    'chunk_index': item.get('chunk_index')
                                },
                                'similarity': similarity
                            })
                
                search_time = time.time() - start_time
                logger.info(f"ContentService: Found {len(processed_results)} results via vector search in {search_time:.3f}s")
                return processed_results
            
            # No results found
            search_time = time.time() - start_time
            logger.info(f"ContentService: No results found for query '{query}' in {search_time:.3f}s")
            return []
            
        except asyncio.TimeoutError:
            logger.warning("Vector search timed out after 3 seconds")
            return []
        except Exception as e:
            logger.error(f"ContentService: Content search failed: {e}")
            return []

    async def delete_content_chunks(self, file_id: str) -> bool:
        """Delete all chunks associated with a file_id"""
        try:
            print(f"\n🗑️  Deleting chunks for file: {file_id}")
            
            if file_id == "clear-all":
                # Clear all chunks
                result = self.supabase.table('content_chunks').delete().neq('id', 0).execute()
                print("✅ Successfully cleared all chunks")
                return True
            
            # Delete chunks from content_chunks table
            result = self.supabase.table('content_chunks').delete().eq('file_id', file_id).execute()
            print(f"✅ Successfully deleted chunks for file: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete chunks for file {file_id}: {e}")
            print(f"❌ Error deleting chunks: {str(e)}")
            return False

    async def get_storage_usage(self) -> Dict[str, Any]:
        """Get storage usage statistics"""
        try:
            # Get total chunks count
            chunks_result = self.supabase.table('content_chunks').select('count').execute()
            total_chunks = chunks_result.data[0]['count'] if chunks_result.data else 0
            
            # Get total files count
            files_result = self.supabase.table('content_files').select('count').execute()
            total_files = files_result.data[0]['count'] if files_result.data else 0
            
            # Get storage size (approximate)
            # Each chunk has embedding (1536 floats * 4 bytes) + content (text)
            avg_chunk_size = 1536 * 4 + 2000  # Approximate size in bytes
            total_size_bytes = total_chunks * avg_chunk_size
            
            return {
                'total_chunks': total_chunks,
                'total_files': total_files,
                'total_size_mb': round(total_size_bytes / (1024 * 1024), 2),
                'avg_chunk_size_kb': round(avg_chunk_size / 1024, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage usage: {e}")
            return {
                'total_chunks': 0,
                'total_files': 0,
                'total_size_mb': 0,
                'avg_chunk_size_kb': 0
            }

    async def cleanup_old_content(self, days: int = 7) -> Dict[str, Any]:
        """Clean up content older than specified days"""
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            # Get files to delete
            old_files = self.supabase.table('content_files')\
                .select('file_id')\
                .lt('uploaded_at', cutoff_date)\
                .execute()
            
            deleted_count = 0
            failed_count = 0
            
            for file in old_files.data:
                if await self.delete_content_chunks(file['file_id']):
                    deleted_count += 1
                else:
                    failed_count += 1
            
            return {
                'deleted_files': deleted_count,
                'failed_deletions': failed_count,
                'cutoff_date': cutoff_date
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup old content: {e}")
            return {
                'deleted_files': 0,
                'failed_deletions': 0,
                'error': str(e)
            }

    async def optimize_storage(self) -> Dict[str, Any]:
        """Optimize storage by removing duplicate chunks and unused content"""
        try:
            # Get duplicate chunks
            duplicates = self.supabase.rpc(
                'find_duplicate_chunks',
                {'similarity_threshold': 0.95}
            ).execute()
            
            deleted_count = 0
            for dup in duplicates.data:
                # Keep the first occurrence, delete others
                to_delete = dup['chunk_ids'][1:]
                if to_delete:
                    self.supabase.table('content_chunks')\
                        .delete()\
                        .in_('id', to_delete)\
                        .execute()
                    deleted_count += len(to_delete)
            
            return {
                'duplicates_found': len(duplicates.data),
                'duplicates_deleted': deleted_count
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize storage: {e}")
            return {
                'duplicates_found': 0,
                'duplicates_deleted': 0,
                'error': str(e)
            }

    async def clear_all_content(self) -> Dict[str, Any]:
        """Clear all content chunks and reset file statuses"""
        try:
            print("\n🗑️  Clearing all content chunks...")
            
            # Get count before deletion
            count_result = self.supabase.table('content_chunks').select('count').execute()
            total_chunks = count_result.data[0]['count'] if count_result.data else 0
            
            # Delete all chunks
            self.supabase.table('content_chunks').delete().neq('id', 0).execute()
            
            # Update all files to deleted status - use a condition that matches all records
            # Since file_id is UUID, we'll use a condition that always matches
            self.supabase.table('content_files').update({
                'status': 'deleted'
            }).gte('file_id', '00000000-0000-0000-0000-000000000000').execute()
            
            print(f"✅ Successfully cleared {total_chunks} chunks")
            return {
                'status': 'success',
                'message': f'Cleared {total_chunks} chunks',
                'chunks_deleted': total_chunks
            }
            
        except Exception as e:
            logger.error(f"Failed to clear content: {e}")
            print(f"❌ Error clearing content: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'chunks_deleted': 0
            } 