from fastapi import APIRouter, HTTPException, Query
from app.services.google_sheets import fetch_practice_data
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/practice/{sheet_name}", tags=["Practice"])
async def get_practice_questions(
    sheet_name: str,
    limit: int = Query(default=None, ge=1, description="Limit number of questions returned")
):
    """
    Fetch practice questions from a specific sheet in the Practice Spreadsheet.
    
    - **sheet_name**: The exact name of the sheet tab (e.g., "C1_Writing_FITB", "A1.Match the pairs")
    """
    try:
        # Decode URL-encoded sheet name if necessary (FastAPI handles standard decoding, 
        # but spaces/special chars should be passed correctly by client)
        
        logger.info(f"Fetching practice questions for sheet: {sheet_name}")
        
        data = fetch_practice_data(sheet_name=sheet_name)
        
        if not data:
            raise HTTPException(status_code=404, detail=f"No data found for sheet: {sheet_name}")
            
        if limit and len(data) > limit:
            data = data[:limit]
            
        return {
            "sheet": sheet_name,
            "count": len(data),
            "data": data
        }
        
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Server configuration error")
    except Exception as e:
        logger.error(f"Error fetching practice data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
