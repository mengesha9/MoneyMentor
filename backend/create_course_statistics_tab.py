#!/usr/bin/env python3
"""
Create a dedicated course_statistics tab with detailed course data for each user
Each course will be in its own row with user identification
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from googleapiclient.discovery import build
from google.oauth2 import service_account
from app.services.course_statistics_service import CourseStatisticsService
from app.core.database import get_supabase

async def create_course_statistics_tab():
    """Create a dedicated course_statistics tab with detailed course data"""
    
    print("📊 Creating Course Statistics Tab")
    print("=" * 50)
    
    try:
        # Get environment variables
        spreadsheet_id = os.getenv('GOOGLE_SHEET_ID')
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        print(f"📋 Configuration:")
        print(f"   - Spreadsheet ID: {spreadsheet_id}")
        print(f"   - Credentials file: {credentials_path}")
        
        if not spreadsheet_id:
            print("❌ GOOGLE_SHEET_ID not set")
            return
        
        if not credentials_path:
            print("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
            return
        
        # Resolve the path to the credentials file
        backend_dir = Path(__file__).resolve().parent
        credentials_file = backend_dir / credentials_path
        
        if not credentials_file.exists():
            print(f"❌ Credentials file not found: {credentials_file}")
            return
        
        print(f"✅ Credentials file found: {credentials_file}")
        
        # Authenticate and construct service
        print(f"\n🔐 Authenticating with Google Sheets API...")
        credentials = service_account.Credentials.from_service_account_file(
            str(credentials_file),
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        service = build('sheets', 'v4', credentials=credentials)
        print(f"✅ Service built successfully")
        
        # Check if course_statistics tab already exists
        print(f"\n🔍 Checking if 'course_statistics' tab already exists...")
        try:
            spreadsheet_info = service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            existing_sheets = []
            for sheet in spreadsheet_info.get('sheets', []):
                sheet_title = sheet.get('properties', {}).get('title', 'Unknown')
                existing_sheets.append(sheet_title)
            
            if 'course_statistics' in existing_sheets:
                print(f"⚠️  Tab 'course_statistics' already exists")
                print(f"   💡 We'll update the existing tab")
            else:
                print(f"✅ Tab 'course_statistics' does not exist - will create it")
                
        except Exception as e:
            print(f"❌ Failed to check existing sheets: {e}")
            return
        
        # Create the course_statistics tab if it doesn't exist
        if 'course_statistics' not in existing_sheets:
            print(f"\n🚀 Creating new tab 'course_statistics'...")
            try:
                add_sheet_request = {
                    'addSheet': {
                        'properties': {
                            'title': 'course_statistics',
                            'gridProperties': {
                                'rowCount': 1000,
                                'columnCount': 10
                            }
                        }
                    }
                }
                
                body = {
                    'requests': [add_sheet_request]
                }
                
                response = service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body=body
                ).execute()
                
                print(f"✅ Tab 'course_statistics' created successfully!")
                
            except Exception as e:
                print(f"❌ Failed to create tab: {e}")
                return
        else:
            print(f"\n📝 Using existing 'course_statistics' tab")
        
        # Get course statistics data
        print(f"\n📊 Fetching course statistics data...")
        try:
            # Initialize services
            supabase = get_supabase()
            course_stats_service = CourseStatisticsService()
            
            # Get all users with their profiles
            users_result = supabase.table('users').select('id, first_name, last_name, email').execute()
            
            if not users_result.data:
                print("❌ No users found")
                return
            
            print(f"✅ Found {len(users_result.data)} users")
            
            # Prepare headers
            headers = [
                'First Name', 
                'Last Name',
                'Email',
                'Course Name',
                'Total Questions Taken',
                'Score (%)',
                'Current Level',
                'Last Activity'
            ]
            
            # Prepare data rows
            all_course_data = []
            all_course_data.append(headers)  # Add headers as first row
            
            for user in users_result.data:
                user_id = user['id']
                first_name = user.get('first_name', 'Unknown')
                last_name = user.get('last_name', 'User')
                email = user.get('email', '')
                
                print(f"   📊 Processing user: {first_name} {last_name} ({email})")
                
                # Get course statistics for this user
                course_stats = await course_stats_service.calculate_user_course_statistics(user_id)
                
                if course_stats:
                    for course_stat in course_stats:
                        row = [
                            first_name,
                            last_name,
                            email,
                            course_stat.get('course_name', 'Unknown'),
                            course_stat.get('total_questions_taken', 0),
                            course_stat.get('score', 0),
                            course_stat.get('level', 'easy'),
                            course_stat.get('last_activity', 'N/A')
                        ]
                        all_course_data.append(row)
                else:
                    # Add a row showing no course data for this user
                    row = [
                        first_name,
                        last_name,
                        email,
                        'No courses taken',
                        0,
                        0,
                        'N/A',
                        'N/A'
                    ]
                    all_course_data.append(row)
            
            print(f"✅ Generated {len(all_course_data)} rows of course statistics data")
            
            # Clear existing data in the course_statistics tab
            print(f"\n🧹 Clearing existing data in course_statistics tab...")
            try:
                # Get current data to find the last row
                result = service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range='course_statistics!A:A'
                ).execute()
                
                if result.get('values') and len(result['values']) > 1:
                    # Clear all data except headers (from row 2 onwards)
                    clear_range = f'course_statistics!A2:J{len(result["values"])}'
                    service.spreadsheets().values().clear(
                        spreadsheetId=spreadsheet_id,
                        range=clear_range
                    ).execute()
                    print(f"✅ Cleared existing data")
                    
            except Exception as e:
                print(f"⚠️  Could not clear existing data: {e}")
            
            # Write the course statistics data
            print(f"\n📝 Writing course statistics data...")
            try:
                body = {
                    'values': all_course_data
                }
                
                result = service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range='course_statistics!A1:H' + str(len(all_course_data)),
                    valueInputOption='RAW',
                    body=body
                ).execute()
                
                print(f"✅ Course statistics data written successfully!")
                print(f"   - Updated cells: {result.get('updatedCells', 0)}")
                print(f"   - Updated rows: {result.get('updatedRows', 0)}")
                print(f"   - Updated columns: {result.get('updatedColumns', 0)}")
                
            except Exception as e:
                print(f"❌ Failed to write course statistics data: {e}")
                return
            
            # Format the headers (make them bold)
            print(f"\n🎨 Formatting headers...")
            try:
                format_request = {
                    'requests': [{
                        'repeatCell': {
                            'range': {
                                'sheetId': None,  # Will be set by the API
                                'startRowIndex': 0,
                                'endRowIndex': 1,
                                'startColumnIndex': 0,
                                'endColumnIndex': len(headers)
                            },
                            'cell': {
                                'userEnteredFormat': {
                                    'textFormat': {
                                        'bold': True
                                    },
                                    'backgroundColor': {
                                        'red': 0.8,
                                        'green': 0.9,
                                        'blue': 1.0
                                    }
                                }
                            },
                            'fields': 'userEnteredFormat.textFormat,userEnteredFormat.backgroundColor'
                        }
                    }]
                }
                
                # Get the sheet ID for course_statistics
                for sheet in spreadsheet_info.get('sheets', []):
                    if sheet.get('properties', {}).get('title') == 'course_statistics':
                        format_request['requests'][0]['repeatCell']['range']['sheetId'] = sheet.get('properties', {}).get('sheetId')
                        break
                
                service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body=format_request
                ).execute()
                
                print(f"✅ Headers formatted successfully!")
                
            except Exception as e:
                print(f"⚠️  Could not format headers: {e}")
            
            # Verify the data was written correctly
            print(f"\n🔍 Verifying data was written correctly...")
            try:
                result = service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range='course_statistics!A1:H10'  # Read first 10 rows
                ).execute()
                
                values = result.get('values', [])
                print(f"✅ Verification successful!")
                print(f"   - Rows read: {len(values)}")
                print(f"   - Columns per row: {len(values[0]) if values else 0}")
                
                if values:
                    print(f"   📋 Sample data (first 3 rows):")
                    for i, row in enumerate(values[:3]):
                        print(f"     Row {i+1}: {row}")
                
            except Exception as e:
                print(f"❌ Failed to verify data: {e}")
                return
            
        except Exception as e:
            print(f"❌ Failed to fetch course statistics data: {e}")
            return
        
        print(f"\n🎉 Course statistics tab created successfully!")
        print(f"✅ New tab 'course_statistics' with detailed course data")
        print(f"📊 Check your Google Sheet:")
        print(f"   https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
        print(f"   Look for the 'course_statistics' tab")
        print(f"💡 Each course is now in its own row with user identification!")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print(f"   - Error type: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(create_course_statistics_tab())
