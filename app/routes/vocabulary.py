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
    category: Optional[str] = Query(None, description="Category name or slug"),
    limit: Optional[int] = Query(None, description="Maximum number of words"),
    transform: bool = Query(True, description="Transform to flashcard format")
):
    """
    Get vocabulary words with optional filtering.
    Category can be the original name or a URL-friendly slug.
    """
    try:
        words = fetch_vocabulary()
        
        # Apply filters
        if level:
            words = [w for w in words if w.get('CEFR Level', '').upper() == level.upper()]
        
        if category:
            # Match both original category name and slug
            def matches_category(word):
                cat = word.get('Category', '')
                cat_slug = slugify(cat) if cat else ''
                category_lower = category.lower()
                # Match if category contains search term OR slug matches
                return (category_lower in cat.lower()) or (category_lower == cat_slug)
            
            words = [w for w in words if matches_category(w)]
        
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
    level: Optional[str] = Query(None, description="CEFR level (A1, A2, B1, B2, C1, C2)"),
    words_per_lesson: int = Query(10, description="Number of words per lesson")
):
    """Get words for a specific lesson, optionally filtered by CEFR level."""
    try:
        all_words = fetch_vocabulary()
        
        # Filter by level if provided
        if level:
            all_words = [w for w in all_words if w.get('CEFR Level', '').upper() == level.upper()]
        
        start_idx = (lesson_id - 1) * words_per_lesson
        end_idx = start_idx + words_per_lesson
        
        if start_idx >= len(all_words):
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        lesson_words = all_words[start_idx:end_idx]
        transformed = [transform_to_flashcard(w) for w in lesson_words]
        
        return {
            "lesson_id": lesson_id,
            "level": level,
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


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    import re
    # Convert to lowercase
    slug = text.lower()
    # Replace & with 'and'
    slug = slug.replace('&', 'and')
    # Replace spaces and special chars with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug


@router.get("/vocabulary/categories-by-level")
def get_categories_by_level(
    level: Optional[str] = Query(None, description="CEFR level (A1, A2, B1, B2, C1, C2)")
):
    """
    Get categories grouped by CEFR level with word counts.
    If level is provided, returns categories for that level only.
    """
    try:
        words = fetch_vocabulary()
        
        # Filter by level if provided
        if level:
            words = [w for w in words if w.get('CEFR Level', '').upper() == level.upper()]
        
        # Group by category and count words
        category_counts = {}
        category_subcategories = {}
        
        for word in words:
            cat = word.get('Category', '')
            subcat = word.get('Sub Category', '')
            
            if cat:
                if cat not in category_counts:
                    category_counts[cat] = 0
                    category_subcategories[cat] = set()
                category_counts[cat] += 1
                if subcat:
                    category_subcategories[cat].add(subcat)
        
        # Build response
        categories = []
        for cat_name, count in sorted(category_counts.items()):
            categories.append({
                "name": cat_name,
                "slug": slugify(cat_name),
                "wordCount": count,
                "subcategories": sorted(list(category_subcategories[cat_name]))
            })
        
        return {
            "level": level.upper() if level else None,
            "totalCategories": len(categories),
            "categories": categories
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

