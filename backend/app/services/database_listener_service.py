import asyncio
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from app.core.config import settings

logger = logging.getLogger(__name__)

class DatabaseListenerService:
    """Service for listening to PostgreSQL notifications and triggering syncs"""
    
    def __init__(self):
        self.connection = None
        self.is_listening = False
        self.listen_task: Optional[asyncio.Task] = None
        self.sync_callbacks = []
    
    async def start_listening(self):
        """Start listening to database notifications"""
        if self.is_listening:
            logger.warning("Database listener is already running")
            return
        
        self.is_listening = True
        logger.info("Starting database listener service")
        
        # Start the listener task
        self.listen_task = asyncio.create_task(self._listen_loop())
    
    async def stop_listening(self):
        """Stop listening to database notifications"""
        if not self.is_listening:
            return
        
        self.is_listening = False
        logger.info("Stopping database listener service")
        
        if self.listen_task:
            self.listen_task.cancel()
            try:
                await self.listen_task
            except asyncio.CancelledError:
                pass
        
        if self.connection:
            try:
                self.connection.close()
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
    
    async def _listen_loop(self):
        """Main listening loop"""
        while self.is_listening:
            try:
                await self._connect_and_listen()
            except asyncio.CancelledError:
                logger.info("Database listener cancelled")
                break
            except Exception as e:
                logger.error(f"Error in database listener: {e}")
                # Wait before retrying
                await asyncio.sleep(5)
    
    async def _connect_and_listen(self):
        """Connect to database and listen for notifications"""
        try:
            # Parse database URL to get connection parameters
            db_url = settings.SUPABASE_URL.replace('https://', '').replace('.supabase.co', '')
            db_host = f"{db_url}.supabase.co"
            db_name = "postgres"
            db_user = "postgres"
            db_password = settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_KEY
            
            # Create connection
            self.connection = psycopg2.connect(
                host=db_host,
                database=db_name,
                user=db_user,
                password=db_password,
                port=5432
            )
            self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            # Create cursor
            cursor = self.connection.cursor()
            
            # Listen for notifications
            cursor.execute("LISTEN user_profile_updated;")
            logger.info("Listening for user_profile_updated notifications")
            
            # Listen for notifications
            while self.is_listening:
                # Wait for notifications with timeout
                if self.connection.poll():
                    self.connection.notifies.clear()
                    for notify in self.connection.notifies:
                        await self._handle_notification(notify.payload)
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error in database connection: {e}")
            raise
        finally:
            if self.connection:
                try:
                    self.connection.close()
                except Exception as e:
                    logger.error(f"Error closing connection: {e}")
    
    async def _handle_notification(self, payload: str):
        """Handle database notification"""
        try:
            # Parse notification payload
            data = json.loads(payload)
            user_id = data.get('user_id')
            action = data.get('action')
            action_type = data.get('action_type')
            timestamp = data.get('timestamp')
            
            logger.info(f"Received notification: user_id={user_id}, action={action}, action_type={action_type}")
            
            # Trigger sync callbacks
            for callback in self.sync_callbacks:
                try:
                    await callback(user_id, action, action_type, timestamp)
                except Exception as e:
                    logger.error(f"Error in sync callback: {e}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing notification payload: {e}")
        except Exception as e:
            logger.error(f"Error handling notification: {e}")
    
    def add_sync_callback(self, callback):
        """Add a callback function to be called when notifications are received"""
        self.sync_callbacks.append(callback)
        logger.info(f"Added sync callback: {callback.__name__}")
    
    def remove_sync_callback(self, callback):
        """Remove a sync callback"""
        if callback in self.sync_callbacks:
            self.sync_callbacks.remove(callback)
            logger.info(f"Removed sync callback: {callback.__name__}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the listener service"""
        return {
            "is_listening": self.is_listening,
            "connection_active": self.connection is not None and not self.connection.closed,
            "callback_count": len(self.sync_callbacks)
        }

# Global instance
database_listener_service = DatabaseListenerService() 