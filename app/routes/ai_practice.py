from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import re

from app.core.logging import get_logger
from app.services.google_sheets import fetch_ai_practice_topics
from app.services.langgraph_chat import chat, generate_initial_greeting, translate_text

# Initialize logger
logger = get_logger(__name__)

router = APIRouter()


# Pydantic models for chat endpoint
class ChatMessage(BaseModel):
    """Individual chat message."""
    sender: str  # 'user' or 'ai'
    text: str
    correction: Optional[str] = None


class ScenarioInfo(BaseModel):
    """Scenario information for AI context."""
    level: str = "A1"
    formality: str = "casual"
    title: str = ""
    aiPrompt: str = ""
    aiRole: str = ""
    userRole: str = ""


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    message: str
    conversation_history: List[ChatMessage] = []
    scenario: ScenarioInfo


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    ai_response: str
    correction: Optional[str] = None
    conversation_history: List[dict]


class InitialGreetingRequest(BaseModel):
    """Request body for initial greeting endpoint."""
    scenario: ScenarioInfo


class InitialGreetingResponse(BaseModel):
    """Response from initial greeting endpoint."""
    ai_response: str



def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    # Convert to lowercase
    slug = text.lower()
    # Replace & with 'and'
    slug = slug.replace('&', 'and')
    # Replace spaces and special chars with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug


def transform_topic(topic: dict, index: int) -> dict:
    """Transform Google Sheets row to chat topic card format."""
    title = topic.get('Topic', '')
    level = topic.get('Level', 'A1')
    conversation_style = topic.get('Conversation style', 'Casual')
    
    # Map level to difficulty
    level_to_difficulty = {
        'A1': 'beginner',
        'A2': 'beginner',
        'B1': 'intermediate',
        'B2': 'intermediate',
        'C1': 'advanced',
        'C2': 'advanced'
    }
    
    # Generate an icon based on topic content (simple mapping)
    topic_icons = {
        'coffee': '☕',
        'bakery': '🥖',
        'bread': '🥖',
        'hotel': '🏨',
        'direction': '🗺️',
        'doctor': '🏥',
        'clothes': '👕',
        'shopping': '🛍️',
        'restaurant': '🍽️',
        'food': '🍽️',
        'café': '☕',
        'weekend': '🌴',
        'friend': '👋',
        'receptionist': '🏢',
        'appointment': '📅',
        'product': '📦',
        'faulty': '📦',
    }
    
    icon = '💬'  # Default icon
    title_lower = title.lower()
    for keyword, emoji in topic_icons.items():
        if keyword in title_lower:
            icon = emoji
            break
    
    return {
        "id": index + 1,
        "slug": slugify(title),
        "title": title,
        "description": topic.get('Instruction to the user', ''),
        "difficulty": level_to_difficulty.get(level.upper(), 'beginner'),
        "level": level.upper(),
        "formality": conversation_style.lower(),
        "icon": icon,
        "estimatedTime": "5-10 min",
        "messageCount": 10,
        "aiRole": topic.get('Role played by AI', ''),
        "userRole": topic.get('Role played by user', ''),
        "aiPrompt": topic.get('Prompt generated to the AI', ''),
    }


@router.get("/ai-practice/topics")
def get_ai_practice_topics(
    level: Optional[str] = Query(None, description="CEFR level (A1, A2, B1, B2, C1, C2)"),
    formality: Optional[str] = Query(None, description="Conversation style (casual, formal)"),
    limit: Optional[int] = Query(None, description="Maximum number of topics")
):
    """
    Get AI practice chat topics with optional filtering.
    """
    logger.info(f"Fetching AI practice topics | level={level}, formality={formality}, limit={limit}")
    try:
        topics = fetch_ai_practice_topics()
        logger.debug(f"Fetched {len(topics)} topics from Google Sheets")
        
        # Apply filters
        if level:
            topics = [t for t in topics if t.get('Level', '').upper() == level.upper()]
            logger.debug(f"Filtered by level={level}, remaining: {len(topics)} topics")
        
        if formality:
            topics = [t for t in topics if t.get('Conversation style', '').lower() == formality.lower()]
            logger.debug(f"Filtered by formality={formality}, remaining: {len(topics)} topics")
        
        # Transform to frontend format
        transformed = [transform_topic(t, i) for i, t in enumerate(topics)]
        
        if limit:
            transformed = transformed[:limit]
        
        logger.info(f"Returning {len(transformed)} AI practice topics")
        return {
            "count": len(transformed),
            "topics": transformed
        }
    
    except FileNotFoundError as e:
        logger.error(f"Credentials not found: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to fetch AI practice topics")
        raise HTTPException(status_code=500, detail=f"Error fetching AI practice topics: {str(e)}")


@router.get("/ai-practice/topics/{topic_slug}")
def get_topic_by_slug(topic_slug: str):
    """
    Get a specific AI practice topic by its slug.
    """
    logger.info(f"Fetching AI practice topic | slug={topic_slug}")
    try:
        topics = fetch_ai_practice_topics()
        
        for i, topic in enumerate(topics):
            if slugify(topic.get('Topic', '')) == topic_slug:
                transformed = transform_topic(topic, i)
                logger.info(f"Found topic: {transformed['title']}")
                return transformed
        
        logger.warning(f"Topic not found: {topic_slug}")
        raise HTTPException(status_code=404, detail=f"Topic not found: {topic_slug}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to fetch AI practice topic | slug={topic_slug}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai-practice/levels")
def get_available_levels():
    """Get list of available CEFR levels for AI practice topics."""
    logger.info("Fetching available AI practice levels")
    try:
        topics = fetch_ai_practice_topics()
        levels = list(set(t.get('Level', '').upper() for t in topics if t.get('Level')))
        levels.sort()
        logger.info(f"Found {len(levels)} AI practice levels")
        return {"levels": levels}
    except Exception as e:
        logger.exception("Failed to fetch AI practice levels")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-practice/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """
    Send a message in an AI practice conversation.
    
    The AI will respond in French based on the scenario context and user's CEFR level.
    If grammar errors are detected, a correction will be included.
    """
    logger.info(f"Chat request | scenario={request.scenario.title} | level={request.scenario.level}")
    
    try:
        # Convert Pydantic models to dicts for the service
        history = [msg.model_dump() for msg in request.conversation_history]
        scenario = request.scenario.model_dump()
        
        # Call the LangGraph chat service
        result = chat(
            user_message=request.message,
            conversation_history=history,
            scenario=scenario
        )
        
        logger.info(f"Chat response generated | correction={result.get('correction') is not None}")
        
        return ChatResponse(
            ai_response=result["ai_response"],
            correction=result.get("correction"),
            conversation_history=result["conversation_history"]
        )
    
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception("Failed to generate chat response")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.post("/ai-practice/chat/greeting", response_model=InitialGreetingResponse)
async def get_initial_greeting(request: InitialGreetingRequest):
    """
    Generate an initial AI greeting for a new conversation.
    
    This should be called when starting a new chat session to get the AI's
    opening message based on the scenario.
    """
    logger.info(f"Generating initial greeting | scenario={request.scenario.title}")
    
    try:
        scenario = request.scenario.model_dump()
        result = generate_initial_greeting(scenario)
        
        logger.info("Initial greeting generated successfully")
        
        return InitialGreetingResponse(ai_response=result["ai_response"])
    
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception("Failed to generate initial greeting")
        raise HTTPException(status_code=500, detail=f"Greeting error: {str(e)}")


class TranslationRequest(BaseModel):
    """Request body for translation endpoint."""
    text: str
    target_lang: str = "en"


class TranslationResponse(BaseModel):
    """Response from translation endpoint."""
    text: str
    translation: str


@router.post("/ai-practice/translate", response_model=TranslationResponse)
async def translate_text_endpoint(request: TranslationRequest):
    """
    Translate text using the AI model.
    """
    logger.info(f"Translation request | text_len={len(request.text)} | target={request.target_lang}")
    
    try:
        translation = translate_text(request.text, request.target_lang)
        
        return TranslationResponse(
            text=request.text,
            translation=translation
        )
        
    except Exception as e:
        logger.exception("Failed to translate text")
        raise HTTPException(status_code=500, detail=f"Translation error: {str(e)}")
