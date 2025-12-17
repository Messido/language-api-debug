from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.google_sheets import fetch_vocabulary

router = APIRouter()


def transform_to_flashcard(word: dict) -> dict:
    """Transform Google Sheets row to flashcard format."""
    forms = []
    
    # Add masculine form if exists
    if word.get('Masculine'):
        forms.append({
            "word": word['Masculine'],
            "gender": "Masculine ♂",
            "genderColor": "text-sky-500",
            "pronunciation": word.get('Pronunciation - Masculine', '')
        })
    
    # Add feminine form if exists
    if word.get('Feminine'):
        forms.append({
            "word": word['Feminine'],
            "gender": "Feminine ♀",
            "genderColor": "text-pink-500",
            "pronunciation": word.get('Pronunciation - Feminine', '')
        })
    
    # Add no gender form if exists
    if word.get('No Gender'):
        forms.append({
            "word": word['No Gender'],
            "gender": "Neutral",
            "genderColor": "text-gray-500",
            "pronunciation": word.get('Pronunciation - No Gender', '')
        })
    
    return {
        "id": word.get('Unique ID', ''),
        "english": word.get('English Word', ''),
        "forms": forms,
        "exampleTarget": word.get('French Sentence', ''),
        "exampleNative": word.get('English Sentence', ''),
        "phonetic": word.get('Pronunciation', ''),
        "level": word.get('CEFR Level', ''),
        "category": word.get('Category', ''),
        "subCategory": word.get('Sub Category', ''),
        "image": ""  # Placeholder - can be added later
    }


@router.get("/vocabulary")
def get_vocabulary(
    level: Optional[str] = Query(None, description="CEFR level (A1, A2, B1, B2, C1)"),
    category: Optional[str] = Query(None, description="Category name"),
    limit: Optional[int] = Query(None, description="Maximum number of words"),
    transform: bool = Query(True, description="Transform to flashcard format")
):
    """
    Get vocabulary words with optional filtering.
    """
    try:
        words = fetch_vocabulary()
        
        # Apply filters
        if level:
            words = [w for w in words if w.get('CEFR Level', '').upper() == level.upper()]
        
        if category:
            words = [w for w in words if category.lower() in w.get('Category', '').lower()]
        
        if limit:
            words = words[:limit]
        
        # Transform to flashcard format if requested
        if transform:
            words = [transform_to_flashcard(w) for w in words]
        
        return {
            "count": len(words),
            "words": words
        }
    
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching vocabulary: {str(e)}")


@router.get("/vocabulary/lesson/{lesson_id}")
def get_lesson_words(
    lesson_id: int,
    words_per_lesson: int = Query(10, description="Number of words per lesson")
):
    """Get words for a specific lesson."""
    try:
        all_words = fetch_vocabulary()
        
        start_idx = (lesson_id - 1) * words_per_lesson
        end_idx = start_idx + words_per_lesson
        
        if start_idx >= len(all_words):
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        lesson_words = all_words[start_idx:end_idx]
        transformed = [transform_to_flashcard(w) for w in lesson_words]
        
        return {
            "lesson_id": lesson_id,
            "words_per_lesson": words_per_lesson,
            "total_words": len(all_words),
            "total_lessons": (len(all_words) + words_per_lesson - 1) // words_per_lesson,
            "count": len(transformed),
            "words": transformed
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vocabulary/levels")
def get_available_levels():
    """Get list of available CEFR levels."""
    try:
        words = fetch_vocabulary()
        levels = list(set(w.get('CEFR Level', '') for w in words if w.get('CEFR Level')))
        levels.sort()
        return {"levels": levels}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vocabulary/categories")
def get_available_categories():
    """Get list of available categories."""
    try:
        words = fetch_vocabulary()
        categories = list(set(w.get('Category', '') for w in words if w.get('Category')))
        categories.sort()
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
