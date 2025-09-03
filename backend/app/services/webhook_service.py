from typing import Dict, Any
import logging
import aiohttp
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

class WebhookService:
    def __init__(self):
        self.quiz_webhook_url = settings.QUIZ_WEBHOOK_URL
        self.calculation_webhook_url = settings.CALCULATION_WEBHOOK_URL
        self.make_webhook_url = settings.MAKE_WEBHOOK_URL
    
    async def log_quiz_attempt(self, quiz_data: Dict[str, Any]) -> bool:
        """Log quiz attempt to webhook"""
        try:
            payload = {
                "user_id": quiz_data["user_id"],
                "timestamp": datetime.utcnow().isoformat(),
                "quiz_id": quiz_data["quiz_id"],
                "selected_option": quiz_data["selected_option"],
                "correct": quiz_data["correct"],
                "topic_tag": quiz_data["topic_tag"]
            }
            
            # Send to Make.com webhook
            if self.make_webhook_url:
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.make_webhook_url, json=payload) as response:
                        if response.status != 200:
                            logger.error(f"Failed to send quiz data to Make.com: {response.status}")
                            return False
            
            # Send to custom webhook
            if self.quiz_webhook_url:
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.quiz_webhook_url, json=payload) as response:
                        if response.status != 200:
                            logger.error(f"Failed to send quiz data to webhook: {response.status}")
                            return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log quiz attempt: {e}")
            return False
    
    async def log_calculation(self, calc_data: Dict[str, Any]) -> bool:
        """Log calculation to webhook"""
        try:
            payload = {
                "user_id": calc_data["user_id"],
                "timestamp": datetime.utcnow().isoformat(),
                "calculation_type": calc_data["type"],
                "inputs": calc_data["inputs"],
                "result": calc_data["result"]
            }
            
            if self.calculation_webhook_url:
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.calculation_webhook_url, json=payload) as response:
                        if response.status != 200:
                            logger.error(f"Failed to send calculation data to webhook: {response.status}")
                            return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log calculation: {e}")
            return False 