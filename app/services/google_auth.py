import os
import json
from google.oauth2 import service_account
from app.core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Scopes for Google Drive and Sheets
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

def get_credentials():
    """Get Google credentials from environment or file."""
    # Try to load from JSON string in environment (for production)
    credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    
    if credentials_json:
        # Strip whitespace to handle cases where env var might be " " or "\n"
        credentials_json = credentials_json.strip()
        
    if credentials_json:
        logger.debug("Loading credentials from GOOGLE_CREDENTIALS_JSON environment variable")
        try:
            credentials_dict = json.loads(credentials_json)
            return service_account.Credentials.from_service_account_info(
                credentials_dict, scopes=SCOPES
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GOOGLE_CREDENTIALS_JSON: {str(e)}")
            logger.error("Ensure the environment variable contains a valid JSON string.")
            # Fall back to file if JSON is invalid, but log the error clearly
        except Exception as e:
            logger.error(f"Error loading credentials from GOOGLE_CREDENTIALS_JSON: {str(e)}")
            # Fall back to file
    
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
