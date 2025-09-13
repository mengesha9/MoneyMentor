#!/usr/bin/env python3
"""
Check current data in Google Sheets tabs
"""
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_sheet_data():
    """Check data in each Google Sheets tab"""
    try:
        from app.services.google_sheets_service import GoogleSheetsService

        service = GoogleSheetsService()
        sheet_info = service.get_sheet_info()

        if sheet_info:
            print(f"Sheet: {sheet_info['title']}")
            print(f"Available tabs: {sheet_info['sheets']}")
            print()

            # Check data in each tab
            tabs_to_check = ['UserProfiles', 'QuizResponses', 'EngagementLogs', 'ChatLogs', 'CourseProgress', 'course_statistics']

            for tab in tabs_to_check:
                try:
                    result = service.service.spreadsheets().values().get(
                        spreadsheetId=service.spreadsheet_id,
                        range=f'{tab}!A1:Z1000'  # Get more rows to see actual data
                    ).execute()

                    data = result.get('values', [])
                    print(f"{tab}: {len(data)} rows")

                    if data and len(data) > 1:  # Has header + data
                        print(f"  Sample data (first 3 rows):")
                        for i, row in enumerate(data[:4]):  # Show header + 3 data rows
                            print(f"    Row {i}: {row}")
                    elif data and len(data) == 1:  # Only header
                        print(f"  Only headers: {data[0]}")
                    else:
                        print("  No data")
                    print()

                except Exception as e:
                    print(f"{tab}: Error - {e}")
                    print()

                except Exception as e:
                    print(f"{tab}: Error - {e}")
                    print()

        else:
            print("Could not get sheet info")

    except Exception as e:
        logger.error(f"Error checking sheet data: {e}")

if __name__ == "__main__":
    asyncio.run(check_sheet_data())