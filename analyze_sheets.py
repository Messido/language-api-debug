import os
import sys
from dotenv import load_dotenv
from googleapiclient.discovery import build

# Add current directory to path
sys.path.append(os.getcwd())

from app.services.google_auth import get_credentials

def analyze_sheets():
    load_dotenv()
    sheet_id = os.getenv('PRACTICE_SPREADSHEET_ID')
    
    if not sheet_id:
        print("Error: PRACTICE_SPREADSHEET_ID not set")
        return

    try:
        creds = get_credentials()
        service = build('sheets', 'v4', credentials=creds)
        
        # Get spreadsheet metadata
        spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        sheets = spreadsheet.get('sheets', [])
        
        print(f"Found {len(sheets)} sheets.")
        
        # Keywords to look for
        keywords = ["B1", "B2", "B3", "B4", "B5", "B6", "Listening", "Match", "Audio", "Phonetic", "Dictation"]
        
        for sheet in sheets:
            title = sheet['properties']['title']
            
            # Check if relevant
            # if any(k in title for k in keywords):
            # Just print all for now to be safe, or filter lightly
            print(f"\n--- Sheet: {title} ---")
            
            # Fetch headers (Row 1)
            range_name = f"'{title}'!A1:Z1"
            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id, range=range_name).execute()
            
            rows = result.get('values', [])
            if rows:
                print(f"Headers: {rows[0]}")
            else:
                print("Headers: [Empty]")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_sheets()
