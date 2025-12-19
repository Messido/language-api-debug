from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import json
from dotenv import load_dotenv

from app.core.logging import get_logger

load_dotenv()

# Initialize logger
logger = get_logger(__name__)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


def get_credentials():
    """Get Google credentials from environment or file."""
    # Try to load from JSON string in environment (for production)
    credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if credentials_json:
        logger.debug("Loading credentials from GOOGLE_CREDENTIALS_JSON environment variable")
        credentials_dict = json.loads(credentials_json)
        return service_account.Credentials.from_service_account_info(
            credentials_dict, scopes=SCOPES
        )
    
    # Fall back to file (for local development)
    credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
    if os.path.exists(credentials_file):
        logger.debug(f"Loading credentials from file: {credentials_file}")
        return service_account.Credentials.from_service_account_file(
            credentials_file, scopes=SCOPES
        )
    
    logger.error("Google credentials not found - no env var or file available")
    raise FileNotFoundError(
        "Google credentials not found. Set GOOGLE_CREDENTIALS_JSON env var "
        "or provide credentials.json file."
    )


def get_sheets_service():
    """Create and return Google Sheets API service."""
    logger.debug("Creating Google Sheets API service")
    credentials = get_credentials()
    service = build('sheets', 'v4', credentials=credentials)
    return service


def fetch_vocabulary(
    spreadsheet_id: str = None,
    sheet_name: str = None,
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
            logger.error("SPREADSHEET_ID environment variable not set")
            raise ValueError("SPREADSHEET_ID environment variable not set")
    
    if sheet_name is None:
        sheet_name = os.getenv('SHEET_NAME', 'Sheet1')
    
    logger.debug(f"Fetching vocabulary | sheet={sheet_name}, range={range_str}")
    
    try:
        service = get_sheets_service()
        sheet = service.spreadsheets()
        
        # Sheet names with spaces need single quotes
        if ' ' in sheet_name or '-' in sheet_name:
            range_notation = f"'{sheet_name}'!{range_str}"
        else:
            range_notation = f"{sheet_name}!{range_str}"
        
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=range_notation
        ).execute()
        
        rows = result.get('values', [])
        
        if not rows:
            logger.warning("No data found in Google Sheet")
            return []
        
        # Get header row index from env (default 1, meaning first row)
        # Set to 2 if the first row has errors or is not headers
        header_row_index = int(os.getenv('HEADER_ROW', '1')) - 1  # Convert to 0-indexed
        
        if header_row_index >= len(rows):
            logger.warning(f"Header row index {header_row_index + 1} exceeds row count {len(rows)}")
            return []
        
        headers = rows[header_row_index]
        
        # Convert remaining rows to dictionaries
        vocabulary = []
        for row in rows[header_row_index + 1:]:
            # Pad row with empty strings if shorter than headers
            padded_row = row + [''] * (len(headers) - len(row))
            word_dict = dict(zip(headers, padded_row))
            vocabulary.append(word_dict)
        
        logger.debug(f"Successfully fetched {len(vocabulary)} vocabulary items")
        return vocabulary
        
    except Exception as e:
        logger.exception(f"Failed to fetch vocabulary from Google Sheets")
        raise


