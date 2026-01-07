from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

from app.core.logging import get_logger
from app.services.google_auth import get_credentials

load_dotenv()

# Initialize logger
logger = get_logger(__name__)


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


def fetch_ai_practice_topics(
    spreadsheet_id: str = None,
    sheet_name: str = None,
    range_str: str = "A:I"
) -> list[dict]:
    """
    Fetch AI practice topics from Google Sheet.
    
    Args:
        spreadsheet_id: Google Sheet ID (from URL or env var)
        sheet_name: Name of the sheet tab
        range_str: Column range to fetch
    
    Returns:
        List of dictionaries, each representing an AI practice topic
    """
    if spreadsheet_id is None:
        spreadsheet_id = os.getenv('AI_PROMPTS_SPREADSHEET_ID')
        if not spreadsheet_id:
            # Fall back to main spreadsheet if not set
            spreadsheet_id = os.getenv('SPREADSHEET_ID')
        if not spreadsheet_id:
            logger.error("AI_PROMPTS_SPREADSHEET_ID or SPREADSHEET_ID environment variable not set")
            raise ValueError("Spreadsheet ID environment variable not set")
    
    if sheet_name is None:
        sheet_name = os.getenv('AI_PROMPTS_SHEET_NAME', 'Sheet1')
    
    logger.debug(f"Fetching AI practice topics | sheet={sheet_name}, range={range_str}")
    
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
            logger.warning("No data found in AI Practice Google Sheet")
            return []
        
        # Get header row index from env (default 1, meaning first row)
        header_row_index = int(os.getenv('AI_PROMPTS_HEADER_ROW', '1')) - 1  # Convert to 0-indexed
        
        if header_row_index >= len(rows):
            logger.warning(f"Header row index {header_row_index + 1} exceeds row count {len(rows)}")
            return []
        
        headers = rows[header_row_index]
        # Strip whitespace from headers
        headers = [h.strip() if h else '' for h in headers]
        
        # Convert remaining rows to dictionaries
        topics = []
        for row in rows[header_row_index + 1:]:
            # Pad row with empty strings if shorter than headers
            padded_row = row + [''] * (len(headers) - len(row))
            # Strip whitespace from values too
            padded_row = [v.strip() if isinstance(v, str) else v for v in padded_row]
            topic_dict = dict(zip(headers, padded_row))
            topics.append(topic_dict)
        
        logger.debug(f"Successfully fetched {len(topics)} AI practice topics")
        return topics
        
    except Exception as e:
        logger.exception(f"Failed to fetch AI practice topics from Google Sheets")
        raise
