from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

from app.core.logging import get_logger
from app.services.google_auth import get_credentials

load_dotenv()

# Initialize logger
logger = get_logger(__name__)



# Global service cache
_SERVICE = None

def get_sheets_service():
    """Create and return Google Sheets API service (cached)."""
    global _SERVICE
    
    if _SERVICE:
        return _SERVICE
        
    logger.debug("Creating Google Sheets API service")
    credentials = get_credentials()
    _SERVICE = build('sheets', 'v4', credentials=credentials)
    return _SERVICE


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


def fetch_practice_data(
    sheet_name: str,
    range_str: str = "A:Z"
) -> list[dict]:
    """
    Fetch data from the separate Practice Spreadsheet.
    
    Args:
        sheet_name: Name of the sheet tab (e.g., "A1.Match the pairs")
        range_str: Column range to fetch
    
    Returns:
        List of dictionaries with the data
    """
    spreadsheet_id = os.getenv('PRACTICE_SPREADSHEET_ID')
    if not spreadsheet_id:
        logger.error("PRACTICE_SPREADSHEET_ID environment variable not set")
        raise ValueError("PRACTICE_SPREADSHEET_ID environment variable not set")
    
    logger.debug(f"Fetching practice data | sheet={sheet_name}, range={range_str}")
    
    try:
        service = get_sheets_service()
        sheet = service.spreadsheets()
        
        # Proper quoting for sheet names
        if ' ' in sheet_name or '-' in sheet_name or '.' in sheet_name:
            range_notation = f"'{sheet_name}'!{range_str}"
        else:
            range_notation = f"{sheet_name}!{range_str}"
        
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=range_notation
        ).execute()
        
        rows = result.get('values', [])
        
        if not rows:
            logger.warning(f"No data found in Practice Sheet: {sheet_name}")
            return []
        
        # Get header row index (default 1 = first row)
        # Note: Practice sheets might have different header rows. 
        # For now assuming row 1 is headers based on user's confirmation of "A1:F10"
        header_row_index = 0 
        
        # Check if first row is actually metadata (e.g. "Reading + Listening + Image")
        # In the sample read, Row 4 (index 3) seemed to be the real header: ['Level', 'English word', ...]
        # Let's try to detect the header row by looking for "Level" or "ID" or "English word"
        
        best_header_row = 0
        for i, row in enumerate(rows[:5]): # Scan first 5 rows
            row_str = " ".join(str(c) for c in row).lower()
            if any(keyword in row_str for keyword in ["level", "english", "french", "misspelled", "answer", "correct", "exercise", "id"]):
                best_header_row = i
                break
        
        header_row_index = best_header_row
        
        if header_row_index >= len(rows):
            return []
            
        headers = rows[header_row_index]
        # Clean headers
        headers = [h.strip() if h else f"Column_{j}" for j, h in enumerate(headers)]
        
        items = []
        for row in rows[header_row_index + 1:]:
            # Pad row
            padded_row = row + [''] * (len(headers) - len(row))
            item_dict = dict(zip(headers, padded_row))
            
            # Simple validity check - ignore empty rows
            if any(item_dict.values()):
                items.append(item_dict)
        
        logger.debug(f"Successfully fetched {len(items)} practice items from {sheet_name}")
        return items
        
    except Exception as e:
        logger.exception(f"Failed to fetch practice data from {sheet_name}")
        raise
