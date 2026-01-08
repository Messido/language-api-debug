from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import os
import io

from app.core.logging import get_logger
from app.services.google_auth import get_credentials

# Initialize logger
logger = get_logger(__name__)


def get_drive_service():
    """Create and return Google Drive API service."""
    logger.debug("Creating Google Drive API service")
    credentials = get_credentials()
    service = build('drive', 'v3', credentials=credentials)
    return service


def list_html_files(folder_id: str = None) -> list[dict]:
    """
    List HTML files in Google Drive.
    
    Args:
        folder_id: Optional ID of the folder to search in. 
                   If None, uses GOOGLE_DRIVE_FOLDER_ID env var.
                   If that is also not set, searches entire Drive (filtered by name).
    
    Returns:
        List of file dictionaries with 'id', 'name', 'mimeType'.
    """
    if folder_id is None:
        folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        
    logger.info(f"Listing HTML files from Drive | folder_id={folder_id}")
    
    try:
        service = get_drive_service()
        
        # Build query
        query = "mimeType = 'text/html' and trashed = false"
        if folder_id:
            query += f" and '{folder_id}' in parents"
            
        logger.debug(f"Drive query: {query}")
        
        results = service.files().list(
            q=query,
            pageSize=100,
            fields="nextPageToken, files(id, name, mimeType, createdTime, modifiedTime)"
        ).execute()
        
        files = results.get('files', [])
        logger.info(f"Found {len(files)} HTML files")
        return files
        
    except Exception as e:
        logger.exception("Failed to list files from Google Drive")
        raise


def get_file_content(file_id: str) -> str:
    """
    Download file content from Google Drive as string.
    
    Args:
        file_id: ID of the file to download.
    
    Returns:
        String content of the file.
    """
    logger.info(f"Downloading file content | file_id={file_id}")
    
    try:
        service = get_drive_service()
        
        request = service.files().get_media(fileId=file_id)
        file_io = io.BytesIO()
        downloader = MediaIoBaseDownload(file_io, request)
        
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            if status:
                logger.debug(f"Download {int(status.progress() * 100)}%")
                
        # Reset stream position
        file_io.seek(0)
        content = file_io.read().decode('utf-8')
        
        logger.debug(f"Successfully downloaded file | size={len(content)} chars")
        return content
        
    except Exception as e:
        logger.exception(f"Failed to download file content from Google Drive | file_id={file_id}")
        raise
