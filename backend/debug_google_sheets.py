#!/usr/bin/env python3
"""
Debug script to check Google Sheets configuration and access
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_google_sheets_config():
    """Debug Google Sheets configuration"""
    
    print("🔍 Debugging Google Sheets Configuration...")
    print("=" * 60)
    
    # Check environment variables
    print("\n1. Environment Variables:")
    print("   📋 GOOGLE_SHEET_ID:", os.getenv('GOOGLE_SHEET_ID', '❌ NOT SET'))
    print("   📋 GOOGLE_CLIENT_EMAIL:", os.getenv('GOOGLE_CLIENT_EMAIL', '❌ NOT SET'))
    print("   📋 GOOGLE_APPLICATION_CREDENTIALS:", os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '❌ NOT SET'))
    
    # Check if credentials file exists
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if credentials_path:
        backend_dir = Path(__file__).resolve().parent
        credentials_file = backend_dir / credentials_path
        
        print(f"\n2. Credentials File:")
        print(f"   📁 Path: {credentials_file}")
        print(f"   📁 Exists: {'✅ YES' if credentials_file.exists() else '❌ NO'}")
        
        if credentials_file.exists():
            try:
                import json
                with open(credentials_file, 'r') as f:
                    creds = json.load(f)
                
                service_account_email = creds.get('client_email', 'Unknown')
                print(f"   📧 Service Account Email: {service_account_email}")
                print(f"   🔑 Project ID: {creds.get('project_id', 'Unknown')}")
                
            except Exception as e:
                print(f"   ❌ Error reading credentials: {e}")
    
    # Test Google Sheets connection
    print("\n3. Testing Google Sheets Connection:")
    try:
        from app.services.google_sheets_service import GoogleSheetsService
        
        sheets_service = GoogleSheetsService()
        
        if sheets_service.service:
            print("   ✅ Google Sheets service initialized")
            
            # Test connection
            if sheets_service.test_connection():
                print("   ✅ Connection test successful")
                
                # Get sheet info
                sheet_info = sheets_service.get_sheet_info()
                if sheet_info:
                    print(f"   📊 Sheet Title: {sheet_info.get('properties', {}).get('title', 'Unknown')}")
                    print(f"   📊 Sheet ID: {sheet_info.get('spreadsheetId', 'Unknown')}")
                    
                    # List all tabs
                    sheets = sheet_info.get('sheets', [])
                    print(f"   📊 Available Tabs ({len(sheets)}):")
                    for sheet in sheets:
                        title = sheet.get('properties', {}).get('title', 'Unknown')
                        print(f"      • {title}")
                
            else:
                print("   ❌ Connection test failed")
        else:
            print("   ❌ Google Sheets service not initialized")
            
    except Exception as e:
        print(f"   ❌ Error testing connection: {e}")
    
    # Check client email access
    client_email = os.getenv('GOOGLE_CLIENT_EMAIL')
    if client_email:
        print(f"\n4. Client Email Access:")
        print(f"   📧 Email: {client_email}")
        print(f"   💡 This email should have access to the Google Sheets")
        print(f"   💡 Check your email for an invitation to access the spreadsheet")
    
    # Instructions
    print("\n5. Troubleshooting Steps:")
    print("   🔧 If UserProfiles tab is missing:")
    print("      1. Check that GOOGLE_SHEET_ID is correct")
    print("      2. Check that GOOGLE_CLIENT_EMAIL is your email")
    print("      3. Check your email for Google Sheets invitation")
    print("      4. Run: python test_simple_sync.py")
    print("      5. Check the Google Sheets manually")
    
    print("\n   🔧 If you need to set up Google Sheets:")
    print("      1. Create a new Google Sheets")
    print("      2. Copy the spreadsheet ID from the URL")
    print("      3. Set GOOGLE_SHEET_ID in your .env file")
    print("      4. Set GOOGLE_CLIENT_EMAIL to your email in .env file")
    print("      5. Run: python test_simple_sync.py")

if __name__ == "__main__":
    debug_google_sheets_config() 