#!/usr/bin/env python3
"""
Script to read all tabs in Google Sheets and check their current data
"""
import os
import asyncio
import logging

# Set up environment
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './google-credentials.json'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_all_tabs():
    """Check all tabs in the Google Sheet"""
    try:
        from app.services.google_sheets_service import GoogleSheetsService

        service = GoogleSheetsService()
        sheet_info = service.get_sheet_info()

        if sheet_info:
            print(f"Sheet: {sheet_info['title']}")
            print(f"All tabs: {sheet_info['sheets']}")
            print()

            # Check data in each tab
            for tab in sheet_info['sheets']:
                try:
                    result = service.service.spreadsheets().values().get(
                        spreadsheetId=service.spreadsheet_id,
                        range=f'{tab}!A1:Z10'
                    ).execute()

                    data = result.get('values', [])
                    print(f"{tab}: {len(data)} rows")

                    if data and len(data) > 0:
                        print(f"  Headers: {data[0]}")
                        if len(data) > 1:
                            sample = data[1][:5] if len(data[1]) > 5 else data[1]
                            print(f"  Sample data: {sample}")
                    print()

                except Exception as e:
                    print(f"{tab}: Error - {e}")
                    print()

        else:
            print("Could not get sheet info")

    except Exception as e:
        logger.error(f"Error checking tabs: {e}")

if __name__ == "__main__":
    asyncio.run(check_all_tabs())