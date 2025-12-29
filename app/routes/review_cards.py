"""
Review Cards API endpoints.
Handles CRUD operations for user's bookmarked vocabulary cards.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.core.logging import get_logger
from app.services.db import get_collection

logger = get_logger(__name__)

router = APIRouter()


# Pydantic models for request/response
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


class ReviewCardCreate(BaseModel):
    userId: str
    cardId: str
    cardData: CardData


class ReviewCardResponse(BaseModel):
    id: str
    userId: str
    cardId: str
    markedAt: datetime
    lastReviewedAt: Optional[datetime] = None
    reviewCount: int
    status: str
    cardData: CardData


class ReviewCardUpdate(BaseModel):
    status: Optional[str] = None
    lastReviewedAt: Optional[datetime] = None


# Helper to convert MongoDB document to response
def doc_to_response(doc: dict) -> dict:
    """Convert MongoDB document to API response format."""
    return {
        "id": str(doc["_id"]),
        "userId": doc["userId"],
        "cardId": doc["cardId"],
        "markedAt": doc["markedAt"],
        "lastReviewedAt": doc.get("lastReviewedAt"),
        "reviewCount": doc.get("reviewCount", 0),
        "status": doc.get("status", "pending"),
        "cardData": doc["cardData"]
    }


@router.post("/review-cards")
async def add_review_card(card: ReviewCardCreate):
    """
    Add a vocabulary card to user's review list.
    If card already exists for user, returns existing card.
    """
    logger.info(f"Adding review card | userId={card.userId}, cardId={card.cardId}")
    
    try:
        collection = get_collection("review_cards")
        
        # Check if card already exists for this user
        existing = await collection.find_one({
            "userId": card.userId,
            "cardId": card.cardId
        })
        
        if existing:
            logger.info(f"Card already bookmarked | cardId={card.cardId}")
            return {
                "message": "Card already bookmarked",
                "card": doc_to_response(existing)
            }
        
        # Create new review card document
        doc = {
            "userId": card.userId,
            "cardId": card.cardId,
            "markedAt": datetime.utcnow(),
            "lastReviewedAt": None,
            "reviewCount": 0,
            "status": "pending",
            "cardData": card.cardData.model_dump()
        }
        
        result = await collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        
        logger.info(f"Card added to review | cardId={card.cardId}, id={result.inserted_id}")
        return {
            "message": "Card added to review",
            "card": doc_to_response(doc)
        }
        
    except Exception as e:
        logger.exception(f"Failed to add review card | cardId={card.cardId}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/review-cards")
async def get_review_cards(
    user_id: str = Query(..., description="User ID from Clerk"),
    limit: int = Query(20, le=100, description="Max cards to return"),
    cursor: Optional[str] = Query(None, description="Cursor for pagination (ISO timestamp)"),
    status: Optional[str] = Query(None, description="Filter by status: pending, reviewed, mastered")
):
    """
    Get user's review cards with cursor-based pagination.
    Returns cards sorted by markedAt (newest first).
    """
    logger.info(f"Fetching review cards | userId={user_id}, limit={limit}, cursor={cursor}")
    
    try:
        collection = get_collection("review_cards")
        
        # Build query
        query = {"userId": user_id}
        
        if status:
            query["status"] = status
        
        if cursor:
            # Cursor is an ISO timestamp - get cards older than cursor
            cursor_time = datetime.fromisoformat(cursor.replace('Z', '+00:00'))
            query["markedAt"] = {"$lt": cursor_time}
        
        # Fetch one extra to check if there are more
        cards_cursor = collection.find(query).sort("markedAt", -1).limit(limit + 1)
        cards = await cards_cursor.to_list(length=limit + 1)
        
        # Determine if there are more cards
        has_more = len(cards) > limit
        cards = cards[:limit]
        
        # Get next cursor from last card
        next_cursor = None
        if has_more and cards:
            next_cursor = cards[-1]["markedAt"].isoformat()
        
        response_cards = [doc_to_response(c) for c in cards]
        
        logger.info(f"Returning {len(response_cards)} review cards | hasMore={has_more}")
        return {
            "cards": response_cards,
            "nextCursor": next_cursor,
            "hasMore": has_more,
            "count": len(response_cards)
        }
        
    except Exception as e:
        logger.exception(f"Failed to fetch review cards | userId={user_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/review-cards/count")
async def get_review_count(
    user_id: str = Query(..., description="User ID from Clerk"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """Get count of user's review cards."""
    logger.info(f"Getting review card count | userId={user_id}, status={status}")
    
    try:
        collection = get_collection("review_cards")
        
        query = {"userId": user_id}
        if status:
            query["status"] = status
        
        count = await collection.count_documents(query)
        
        logger.info(f"Review card count: {count}")
        return {"count": count}
        
    except Exception as e:
        logger.exception(f"Failed to get count | userId={user_id}")
        raise HTTPException(status_code=500, detail=str(e))


# Bulk Operations Models
class BulkCardItem(BaseModel):
    id: str  # Original vocab ID
    english: str
    forms: List[CardForm]
    exampleTarget: str
    exampleNative: str
    phonetic: str
    level: str
    category: str
    subCategory: Optional[str] = ""
    image: Optional[str] = ""


class ReviewCardBulkCreate(BaseModel):
    userId: str
    level: str
    category: str
    cards: List[BulkCardItem]


@router.post("/review-cards/bulk")
async def bulk_add_review_cards(data: ReviewCardBulkCreate):
    """
    Bulk add cards from a category to review list.
    Skips cards that are already bookmarked.
    """
    logger.info(f"Bulk adding cards | userId={data.userId}, count={len(data.cards)}")
    
    try:
        collection = get_collection("review_cards")
        
        # Prepare operations
        added_count = 0
        timestamp = datetime.utcnow()
        
        for card in data.cards:
            # Check if exists
            existing = await collection.find_one({
                "userId": data.userId,
                "cardId": card.id
            })
            
            if not existing:
                # Create card data object (excluding id)
                card_data_dict = card.model_dump(exclude={"id"})
                
                doc = {
                    "userId": data.userId,
                    "cardId": card.id,
                    "markedAt": timestamp,
                    "lastReviewedAt": None,
                    "reviewCount": 0,
                    "status": "pending",
                    "cardData": card_data_dict
                }
                
                await collection.insert_one(doc)
                added_count += 1
        
        logger.info(f"Bulk add complete | added={added_count}, total={len(data.cards)}")
        return {
            "message": f"Added {added_count} cards to review",
            "addedCount": added_count,
            "totalRequested": len(data.cards)
        }
        
    except Exception as e:
        logger.exception("Failed to bulk add review cards")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/review-cards/bulk")
async def bulk_remove_review_cards(
    user_id: str = Query(..., alias="user_id"),
    level: str = Query(...),
    category: str = Query(...)
):
    """
    Bulk remove all review cards for a specific level usage and category.
    """
    logger.info(f"Bulk removing cards | userId={user_id}, level={level}, category={category}")
    
    try:
        collection = get_collection("review_cards")
        
        # We need to filter by cardData.level and cardData.category
        # MongoDB dot notation for nested fields
        result = await collection.delete_many({
            "userId": user_id,
            "cardData.level": level,
            "cardData.category": category
        })
        
        logger.info(f"Bulk remove complete | deleted={result.deleted_count}")
        return {
            "message": f"Removed {result.deleted_count} cards from review",
            "deletedCount": result.deleted_count
        }
        
    except Exception as e:
        logger.exception("Failed to bulk remove review cards")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/review-cards/check-category")
async def check_category_bookmarked(
    user_id: str = Query(..., alias="user_id"),
    level: str = Query(...),
    category: str = Query(...)
):
    """
    Check if a category is bookmarked (has any cards in review)
    and return the count of bookmarked cards in this category.
    """
    try:
        collection = get_collection("review_cards")
        
        count = await collection.count_documents({
            "userId": user_id,
            "cardData.level": level,
            "cardData.category": category
        })
        
        return {
            "isBookmarked": count > 0,
            "bookmarkedCount": count
        }
        
    except Exception as e:
        logger.exception("Failed to check category bookmark")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/review-cards/check/{card_id}")
async def check_is_bookmarked(
    card_id: str,
    user_id: str = Query(..., description="User ID from Clerk")
):
    """Check if a specific card is bookmarked by the user."""
    logger.info(f"Checking bookmark | userId={user_id}, cardId={card_id}")
    
    try:
        collection = get_collection("review_cards")
        
        existing = await collection.find_one({
            "userId": user_id,
            "cardId": card_id
        })
        
        return {"isBookmarked": existing is not None}
        
    except Exception as e:
        logger.exception(f"Failed to check bookmark | cardId={card_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/review-cards/{card_id}")
async def remove_review_card(
    card_id: str,
    user_id: str = Query(..., description="User ID from Clerk")
):
    """Remove a card from user's review list."""
    logger.info(f"Removing review card | userId={user_id}, cardId={card_id}")
    
    try:
        collection = get_collection("review_cards")
        
        result = await collection.delete_one({
            "userId": user_id,
            "cardId": card_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Card not found in review list")
        
        logger.info(f"Card removed from review | cardId={card_id}")
        return {"message": "Card removed from review"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to remove review card | cardId={card_id}")
        raise HTTPException(status_code=500, detail=str(e))


        if not result:
            raise HTTPException(status_code=404, detail="Card not found in review list")
        
        logger.info(f"Status updated | cardId={card_id}, status={status}")
        return {
            "message": "Status updated",
            "card": doc_to_response(result)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update status | cardId={card_id}")
        raise HTTPException(status_code=500, detail=str(e))



