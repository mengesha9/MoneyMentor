#!/usr/bin/env python3
"""
Manual Session Cleanup Script
Run this script periodically to clean up old empty sessions
"""

import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    """Run session cleanup"""
    try:
        from app.services.session_cleanup_service import session_cleanup_service
        
        logger.info("🧹 Starting manual session cleanup...")
        
        # Force cleanup
        result = await session_cleanup_service.force_cleanup_now()
        
        if result["success"]:
            logger.info(f"✅ Session cleanup completed: {result['message']}")
        else:
            logger.error(f"❌ Session cleanup failed: {result['message']}")
            
    except Exception as e:
        logger.error(f"❌ Error running session cleanup: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 