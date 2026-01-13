import os
import sys
from dotenv import load_dotenv
from googleapiclient.discovery import build

# Add current directory to path
sys.path.append(os.getcwd())

from app.services.google_auth import get_credentials

def detail_analyze_sheets():
    load_dotenv()
    sheet_id = os.getenv('PRACTICE_SPREADSHEET_ID')
    
    if not sheet_id:
        print("Error: PRACTICE_SPREADSHEET_ID not set")
        return

    try:
        creds = get_credentials()
        service = build('sheets', 'v4', credentials=creds)
        
        target_sheets = [
            "A1.Match the pairs",
            "A1_Match the pairs" # Backup guess
        ]
        
        # Get all sheet titles first to match loosely
        spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        all_sheets = [s['properties']['title'] for s in spreadsheet.get('sheets', [])]
        
        print(f"Available Sheets: {all_sheets}")

        for target in target_sheets:
            # Find best match
            actual_name = next((s for s in all_sheets if target.lower() in s.lower()), None)
            
            if actual_name:
                print(f"\n--- Detailed Dump: {actual_name} ---")
                range_name = f"'{actual_name}'!A1:Z5"
                result = service.spreadsheets().values().get(
                    spreadsheetId=sheet_id, range=range_name).execute()
                
                rows = result.get('values', [])
                if not rows:
                    print("Status: COMPLETELY EMPTY (0 rows)")
                else:
                    for i, row in enumerate(rows):
                        print(f"Row {i+1}: {row}")
            else:
                print(f"\n--- Sheet '{target}' NOT FOUND in sheet list ---")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    detail_analyze_sheets()
