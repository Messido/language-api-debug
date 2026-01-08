from dotenv import load_dotenv
import os
import sys

# Add current directory to path so we can import app modules
sys.path.append(os.getcwd())

from app.services.google_auth import get_credentials
from googleapiclient.discovery import build

def test_access():
    load_dotenv()
    
    sheet_id = os.getenv('PRACTICE_SPREADSHEET_ID')
    print(f"Testing access for Sheet ID: {sheet_id}")
    
    if not sheet_id:
        print("ERROR: PRACTICE_SPREADSHEET_ID is missing in .env")
        return

    try:
        creds = get_credentials()
        service = build('sheets', 'v4', credentials=creds)
        
        # Test reading 'A1.Match the pairs'
        sheet_name = "A1.Match the pairs"
        range_name = f"'{sheet_name}'!A1:F10"
        
        print(f"Attempting to read: {range_name}")
        
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range=range_name).execute()
            
        values = result.get('values', [])
        
        if not values:
            print("Connected, but found no data.")
        else:
            print("SUCCESS! Data retrieved:")
            for row in values:
                print(row)
                
    except Exception as e:
        print(f"FAILED to access sheet: {e}")

if __name__ == "__main__":
    test_access()
