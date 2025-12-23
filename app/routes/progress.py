"""
Progress Tracking API endpoints.
Handles saving/retrieving learned cards for user progress.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.core.logging import get_logger
from app.services.db import get_collection

logger = get_logger(__name__)

router = APIRouter()


# Pydantic models
class CardForm(BaseModel):
    word: str
    gender: str
    genderColor: str
    pronunciation: str


class CardData(BaseModel):
    english: str
    forms: List[CardForm]
    exampleTarget: str
    exampleNative: str
    phonetic: str
    level: str
    category: str
    subCategory: Optional[str] = ""
    image: Optional[str] = ""


class LearnedCard(BaseModel):
    cardId: str
    cardData: CardData


class SaveProgressRequest(BaseModel):
    userId: str
    level: str
    category: str
    cards: List[LearnedCard]


# Helper to convert MongoDB document to response
def doc_to_response(doc: dict) -> dict:
    """Convert MongoDB document to API response format."""
    return {
        "id": str(doc["_id"]),
        "userId": doc["userId"],
        "cardId": doc["cardId"],
        "level": doc["level"],
        "category": doc["category"],
        "learnedAt": doc["learnedAt"],
        "lastViewedAt": doc.get("lastViewedAt"),
        "cardData": doc["cardData"]
    }


@router.post("/progress/save")
async def save_progress(request: SaveProgressRequest):
    """
    Batch save learned cards. Uses upsert to avoid duplicates.
    Cards already learned will have their lastViewedAt updated.
    """
    logger.info(f"Saving progress | userId={request.userId}, level={request.level}, "
                f"category={request.category}, cardCount={len(request.cards)}")
    
    try:
        collection = get_collection("learned_cards")
        now = datetime.utcnow()
        
        saved_count = 0
        updated_count = 0
        
        for card in request.cards:
            # Use upsert to insert or update
            result = await collection.update_one(
                {
                    "userId": request.userId,
                    "cardId": card.cardId
                },
                {
                    "$set": {
                        "level": request.level,
                        "category": request.category,
                        "lastViewedAt": now,
                        "cardData": card.cardData.model_dump()
                    },
                    "$setOnInsert": {
                        "learnedAt": now
                    }
                },
                upsert=True
            )
            
            if result.upserted_id:
                saved_count += 1
            else:
                updated_count += 1
        
        logger.info(f"Progress saved | new={saved_count}, updated={updated_count}")
        return {
            "message": "Progress saved",
            "savedCount": saved_count,
            "updatedCount": updated_count,
            "totalCards": len(request.cards)
        }
        
    except Exception as e:
        logger.exception(f"Failed to save progress | userId={request.userId}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/lesson")
async def get_lesson_progress(
    user_id: str = Query(..., description="User ID from Clerk"),
    level: str = Query(..., description="CEFR level"),
    category: str = Query(..., description="Category slug")
):
    """
    Get progress for a specific lesson.
    Returns the count of learned cards and their IDs for resume.
    """
    logger.info(f"Getting lesson progress | userId={user_id}, level={level}, category={category}")
    
    try:
        collection = get_collection("learned_cards")
        
        # Get count of learned cards for this lesson
        count = await collection.count_documents({
            "userId": user_id,
            "level": level.upper(),
            "category": category
        })
        
        # Get card IDs for resume logic
        cursor = collection.find(
            {
                "userId": user_id,
                "level": level.upper(),
                "category": category
            },
            {"cardId": 1}
        )
        cards = await cursor.to_list(length=1000)
        card_ids = [c["cardId"] for c in cards]
        
        logger.info(f"Lesson progress | count={count}")
        return {
            "level": level.upper(),
            "category": category,
            "learnedCount": count,
            "learnedCardIds": card_ids
        }
        
    except Exception as e:
        logger.exception(f"Failed to get lesson progress")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/wordlist")
async def get_wordlist(
    user_id: str = Query(..., description="User ID from Clerk"),
    limit: int = Query(50, le=100, description="Max cards to return"),
    cursor: Optional[str] = Query(None, description="Cursor for pagination (ISO timestamp)")
):
    """
    Get all learned cards for user's wordlist (paginated).
    Returns cards sorted by learnedAt (newest first).
    """
    logger.info(f"Getting wordlist | userId={user_id}, limit={limit}")
    
    try:
        collection = get_collection("learned_cards")
        
        query = {"userId": user_id}
        
        if cursor:
            cursor_time = datetime.fromisoformat(cursor.replace('Z', '+00:00'))
            query["learnedAt"] = {"$lt": cursor_time}
        
        # Fetch one extra for pagination
        cards_cursor = collection.find(query).sort("learnedAt", -1).limit(limit + 1)
        cards = await cards_cursor.to_list(length=limit + 1)
        
        has_more = len(cards) > limit
        cards = cards[:limit]
        
        next_cursor = None
        if has_more and cards:
            next_cursor = cards[-1]["learnedAt"].isoformat()
        
        response_cards = [doc_to_response(c) for c in cards]
        
        logger.info(f"Returning {len(response_cards)} wordlist cards")
        return {
            "cards": response_cards,
            "nextCursor": next_cursor,
            "hasMore": has_more,
            "count": len(response_cards)
        }
        
    except Exception as e:
        logger.exception(f"Failed to get wordlist")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/progress/lesson")
async def reset_lesson_progress(
    user_id: str = Query(..., description="User ID from Clerk"),
    level: str = Query(..., description="CEFR level"),
    category: str = Query(..., description="Category slug")
):
    """
    Reset progress for a specific lesson.
    Deletes all learned cards for this user/level/category.
    """
    logger.info(f"Resetting lesson progress | userId={user_id}, level={level}, category={category}")
    
    try:
        collection = get_collection("learned_cards")
        
        result = await collection.delete_many({
            "userId": user_id,
            "level": level.upper(),
            "category": category
        })
        
        logger.info(f"Deleted {result.deleted_count} cards")
        return {
            "message": "Progress reset",
            "deletedCount": result.deleted_count
        }
        
    except Exception as e:
        logger.exception(f"Failed to reset progress")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/count")
async def get_total_learned_count(
    user_id: str = Query(..., description="User ID from Clerk")
):
    """Get total count of learned cards for user."""
    logger.info(f"Getting total learned count | userId={user_id}")
    
    try:
        collection = get_collection("learned_cards")
        count = await collection.count_documents({"userId": user_id})
        
        return {"count": count}
        
    except Exception as e:
        logger.exception(f"Failed to get count")
        raise HTTPException(status_code=500, detail=str(e))
