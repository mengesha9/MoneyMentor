import asyncio
import json
import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger(__name__)

class SupabaseListenerService:
    """Service for listening to Supabase real-time changes using subscriptions"""
    
    def __init__(self):
        self.supabase: Optional[Client] = None
        self.is_listening = False
        self.listen_task: Optional[asyncio.Task] = None
        self.sync_callbacks = []
        self.subscriptions = {}
    
    async def start_listening(self):
        """Start listening to Supabase real-time changes"""
        if self.is_listening:
            logger.warning("Supabase listener is already running")
            return
        
        self.is_listening = True
        logger.info("Starting Supabase real-time listener service")
        
        # Initialize Supabase client
        self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        # Start the listener task
        self.listen_task = asyncio.create_task(self._listen_loop())
        
        logger.info("Supabase real-time listener started")
    
    async def stop_listening(self):
        """Stop listening to Supabase real-time changes"""
        if not self.is_listening:
            return
        
        self.is_listening = False
        logger.info("Stopping Supabase real-time listener service")
        
        # Remove all subscriptions
        for table, subscription in self.subscriptions.items():
            try:
                self.supabase.remove_channel(subscription)
                logger.info(f"Removed subscription for table: {table}")
            except Exception as e:
                logger.error(f"Error removing subscription for {table}: {e}")
        
        self.subscriptions.clear()
        
        if self.listen_task:
            self.listen_task.cancel()
            try:
                await self.listen_task
            except asyncio.CancelledError:
                pass
    
    async def _listen_loop(self):
        """Main listening loop for Supabase real-time changes"""
        try:
            # Subscribe to user_profiles table changes
            await self._subscribe_to_user_profiles()
            
            # Keep the listener alive
            while self.is_listening:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("Supabase listener cancelled")
        except Exception as e:
            logger.error(f"Error in Supabase listener loop: {e}")
    
    async def _subscribe_to_user_profiles(self):
        """Subscribe to user_profiles table changes"""
        try:
            if not self.supabase:
                logger.error("Supabase client not initialized")
                return
            
            # Use the correct Supabase real-time API
            # The current Python client doesn't support .on() method
            # Instead, we'll use a polling approach that's more reliable
            logger.info("Using polling approach for user_profiles changes (more reliable)")
            
            # Start a polling task instead of real-time subscription
            asyncio.create_task(self._poll_user_profiles_changes())
            
        except Exception as e:
            logger.error(f"Error setting up user_profiles monitoring: {e}")
    
    async def _poll_user_profiles_changes(self):
        """Poll for user_profiles changes every 30 seconds"""
        last_check = None
        
        while self.is_listening:
            try:
                # Get current timestamp
                current_time = datetime.now()
                
                # Query for recent changes
                query = self.supabase.table('user_profiles').select('*')
                if last_check:
                    query = query.gte('updated_at', last_check.isoformat())
                
                result = query.execute()
                
                if result.data:
                    for profile in result.data:
                        # Trigger sync callbacks for each changed profile
                        await self._trigger_sync_callbacks(
                            user_id=str(profile.get('user_id')),
                            action='update',
                            action_type='profile_update',
                            timestamp=profile.get('updated_at', current_time.isoformat())
                        )
                
                last_check = current_time
                
                # Wait 30 seconds before next check
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error polling user_profiles: {e}")
                await asyncio.sleep(30)  # Wait before retrying
    
    def _handle_user_profile_change(self, payload):
        """Handle user profile changes from Supabase real-time"""
        try:
            logger.info(f"Received user profile change: {payload}")
            
            # Extract relevant data from the payload
            event_type = payload.get('eventType')  # 'INSERT' or 'UPDATE'
            table = payload.get('table')
            record = payload.get('record', {})
            old_record = payload.get('oldRecord', {})
            
            if table == 'user_profiles':
                user_id = record.get('user_id')
                if user_id:
                    # Trigger sync callbacks
                    asyncio.create_task(self._trigger_sync_callbacks(
                        user_id=user_id,
                        action=event_type.lower(),
                        action_type='profile_update',
                        timestamp=datetime.now().isoformat(),
                        record=record,
                        old_record=old_record
                    ))
            
        except Exception as e:
            logger.error(f"Error handling user profile change: {e}")
    
    async def _trigger_sync_callbacks(self, user_id: str, action: str, action_type: str, 
                                    timestamp: str, record: Dict = None, old_record: Dict = None):
        """Trigger sync callbacks with user profile change data"""
        try:
            logger.info(f"Triggering sync callbacks for user {user_id}, action: {action}")
            
            for callback in self.sync_callbacks:
                try:
                    await callback(user_id, action, action_type, timestamp)
                except Exception as e:
                    logger.error(f"Error in sync callback: {e}")
            
        except Exception as e:
            logger.error(f"Error triggering sync callbacks: {e}")
    
    def add_sync_callback(self, callback: Callable):
        """Add a callback function to be called when user profiles change"""
        self.sync_callbacks.append(callback)
        logger.info(f"Added sync callback: {callback.__name__}")
    
    def remove_sync_callback(self, callback: Callable):
        """Remove a sync callback"""
        if callback in self.sync_callbacks:
            self.sync_callbacks.remove(callback)
            logger.info(f"Removed sync callback: {callback.__name__}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the listener service"""
        return {
            "is_listening": self.is_listening,
            "subscription_count": len(self.subscriptions),
            "callback_count": len(self.sync_callbacks),
            "active_subscriptions": list(self.subscriptions.keys())
        }

# Global instance
supabase_listener_service = SupabaseListenerService() 