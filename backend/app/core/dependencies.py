from app.services.content_service import ContentService

def get_content_service() -> ContentService:
    """Get ContentService instance"""
    return ContentService() 