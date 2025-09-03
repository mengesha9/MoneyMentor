#!/usr/bin/env python3

import os
from app.core.config import settings
from app.services.google_sheets_service import GoogleSheetsService

def test_google_sheets_connection():
    print("🔍 Testing Google Sheets Connection...")
    
    # Set environment variables from settings
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.GOOGLE_APPLICATION_CREDENTIALS
    os.environ['GOOGLE_SHEET_ID'] = settings.GOOGLE_SHEET_ID
    os.environ['GOOGLE_CLIENT_EMAIL'] = settings.GOOGLE_CLIENT_EMAIL
    
    print(f"📋 Credentials file: {settings.GOOGLE_APPLICATION_CREDENTIALS}")
    print(f"📊 Spreadsheet ID: {settings.GOOGLE_SHEET_ID}")
    print(f"👤 Client email: {settings.GOOGLE_CLIENT_EMAIL}")
    
    try:
        # Initialize service
        service = GoogleSheetsService()
        
        if not service.service:
            print("❌ Google Sheets service not initialized")
            return False
            
        print("✅ Google Sheets service initialized successfully")
        
        # Test access to the spreadsheet
        sheet_info = service.service.spreadsheets().get(
            spreadsheetId=service.spreadsheet_id
        ).execute()
        
        print(f"✅ Successfully accessed Google Sheet: {sheet_info.get('properties', {}).get('title', 'Unknown')}")
        
        # List available sheets
        sheets = [sheet['properties']['title'] for sheet in sheet_info.get('sheets', [])]
        print(f"📋 Available sheets: {sheets}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to access Google Sheets: {e}")
        return False

if __name__ == "__main__":
    success = test_google_sheets_connection()
    if success:
        print("\n🎉 Google Sheets connection is working correctly!")
    else:
        print("\n💥 Google Sheets connection failed!")
