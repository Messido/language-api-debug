from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import json
from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


def get_credentials():
    """Get Google credentials from environment or file."""
    # Try to load from JSON string in environment (for production)
    credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if credentials_json:
        credentials_dict = json.loads(credentials_json)
        return service_account.Credentials.from_service_account_info(
            credentials_dict, scopes=SCOPES
        )
    
    # Fall back to file (for local development)
    credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
    if os.path.exists(credentials_file):
        return service_account.Credentials.from_service_account_file(
            credentials_file, scopes=SCOPES
        )
    
    raise FileNotFoundError(
        "Google credentials not found. Set GOOGLE_CREDENTIALS_JSON env var "
        "or provide credentials.json file."
    )


def get_sheets_service():
    """Create and return Google Sheets API service."""
    credentials = get_credentials()
    service = build('sheets', 'v4', credentials=credentials)
    return service


def fetch_vocabulary(
    spreadsheet_id: str = None,
    sheet_name: str = "Sheet1",
    range_str: str = "A:T"
) -> list[dict]:
    """
    Fetch vocabulary data from Google Sheet.
    
    Args:
        spreadsheet_id: Google Sheet ID (from URL or env var)
        sheet_name: Name of the sheet tab
        range_str: Column range to fetch
    
    Returns:
        List of dictionaries, each representing a vocabulary word
    """
    if spreadsheet_id is None:
        spreadsheet_id = os.getenv('SPREADSHEET_ID')
        if not spreadsheet_id:
            raise ValueError("SPREADSHEET_ID environment variable not set")
    
    service = get_sheets_service()
    sheet = service.spreadsheets()
    
    result = sheet.values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!{range_str}"
    ).execute()
    
    rows = result.get('values', [])
    
    if not rows:
        return []
    
    # First row contains headers
    headers = rows[0]
    
    # Convert remaining rows to dictionaries
    vocabulary = []
    for row in rows[1:]:
        # Pad row with empty strings if shorter than headers
        padded_row = row + [''] * (len(headers) - len(row))
        word_dict = dict(zip(headers, padded_row))
        vocabulary.append(word_dict)
    
    return vocabulary
