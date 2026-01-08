from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.core.logging import get_logger
from app.services.google_drive import list_html_files, get_file_content

# Initialize logger
logger = get_logger(__name__)

router = APIRouter()


@router.get("/grammar/notes")
def get_grammar_notes(
    folder_id: Optional[str] = Query(None, description="Optional Google Drive folder ID")
):
    """
    List available grammar notes (HTML files) from Google Drive.
    """
    logger.info("Fetching grammar notes list")
    try:
        notes = list_html_files(folder_id)
        
        # Sort by name
        notes.sort(key=lambda x: x.get('name', ''))
        
        return {
            "count": len(notes),
            "notes": notes
        }
    except Exception as e:
        logger.exception("Failed to fetch grammar notes")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/grammar/notes/{note_id}")
def get_grammar_note_content(note_id: str):
    """
    Get the HTML content of a specific grammar note.
    """
    logger.info(f"Fetching content for grammar note | id={note_id}")
    try:
        content = get_file_content(note_id)
        
        return {
            "id": note_id,
            "content": content
        }
    except Exception as e:
        logger.exception(f"Failed to fetch grammar note content | id={note_id}")
        raise HTTPException(status_code=500, detail=str(e))
