"""
Student Profile API endpoints.
Handles creation and retrieval of student profiles.
"""

from fastapi import APIRouter, HTTPException, Query, Body, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import random

from app.core.logging import get_logger
from app.services.db import get_collection

logger = get_logger(__name__)

router = APIRouter()

# --- Pydantic Models ---

class ExamIntent(BaseModel):
    hasExam: bool
    examType: Optional[str] = None

class StudentProfileCreate(BaseModel):
    clerkUserId: str
    name: Optional[str] = None
    targetLanguage: str
    instructionLanguage: str
    purpose: List[str]
    examIntent: ExamIntent
    level: str
    levelSource: str  # "beginner" | "manual" | "test"

class StudentProfileResponse(BaseModel):
    id: str  # MongoDB _id
    clerkUserId: str
    studentId: str  # S-123456
    name: Optional[str] = None
    targetLanguage: str
    instructionLanguage: str
    purpose: List[str]
    examIntent: ExamIntent
    level: str
    levelSource: str
    createdAt: datetime
    updatedAt: datetime
    role: str = "student"

class OnboardingStatus(BaseModel):
    isComplete: bool
    studentId: Optional[str] = None
    role: Optional[str] = None

# --- Helper Functions ---

def generate_student_id() -> str:
    """Generate a random Student ID starting with S-."""
    # Generate 6 random digits
    digits = random.randint(100000, 999999)
    return f"S-{digits}"

def doc_to_response(doc: dict) -> dict:
    """Convert MongoDB document to API response."""
    return {
        "id": str(doc["_id"]),
        "clerkUserId": doc["clerkUserId"],
        "studentId": doc["studentId"],
        "name": doc.get("name"),
        "targetLanguage": doc["targetLanguage"],
        "instructionLanguage": doc["instructionLanguage"],
        "purpose": doc["purpose"],
        "examIntent": doc["examIntent"],
        "level": doc["level"],
        "levelSource": doc["levelSource"],
        "createdAt": doc["createdAt"],
        "updatedAt": doc.get("updatedAt", doc["createdAt"]),
        "role": doc.get("role", "student")
    }

# --- Routes ---

@router.post("/students", response_model=StudentProfileResponse)
async def create_student_profile(profile: StudentProfileCreate):
    """
    Create a new student profile after onboarding.
    Auto-generates a Student ID (S-xxxxxx).
    """
    logger.info(f"Creating student profile | userId={profile.clerkUserId}")

    try:
        collection = get_collection("students")

        # Check if profile already exists
        existing = await collection.find_one({"clerkUserId": profile.clerkUserId})
        if existing:
            logger.info(f"Student profile already exists | userId={profile.clerkUserId}")
            return doc_to_response(existing)

        # Generate unique Student ID
        # In a high-concurrency real app, we'd check for uniqueness collision
        student_id = generate_student_id()

        # Create document
        doc = {
            "clerkUserId": profile.clerkUserId,
            "studentId": student_id,
            "name": profile.name,
            "targetLanguage": profile.targetLanguage,
            "instructionLanguage": profile.instructionLanguage,
            "purpose": profile.purpose,
            "examIntent": profile.examIntent.model_dump(),
            "level": profile.level,
            "levelSource": profile.levelSource,
            "role": "student",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }

        result = await collection.insert_one(doc)
        doc["_id"] = result.inserted_id

        logger.info(f"Student profile created | userId={profile.clerkUserId}, studentId={student_id}")
        return doc_to_response(doc)

    except Exception as e:
        logger.exception(f"Failed to create student profile | userId={profile.clerkUserId}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/students/me", response_model=StudentProfileResponse)
async def get_my_profile(
    user_id: str = Query(..., description="Clerk User ID")
):
    """Get current user's student profile."""
    logger.info(f"Fetching student profile | userId={user_id}")

    try:
        collection = get_collection("students")
        doc = await collection.find_one({"clerkUserId": user_id})

        if not doc:
            raise HTTPException(status_code=404, detail="Profile not found")

        return doc_to_response(doc)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to fetch profile | userId={user_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/students/placement-test")
async def get_placement_test(
    language: str = Query(..., description="Target language (e.g., French)"),
    source_language: str = Query("English", description="Source language")
):
    """Get placement test questions for a specific language pair."""
    
    if language.lower() != "french":
        # MVP only supports French
        return {"questions": []}
        
    # Hardcoded questions for MVP (English -> French)
    questions = [
        {
            "id": 1,
            "question": "How do you say 'Hello' in French?",
            "options": ["Au revoir", "Bonjour", "Merci", "S'il vous plaît"],
            "correctAnswer": "Bonjour",
            "difficulty": "A1"
        },
        {
            "id": 2,
            "question": "Translate: 'One coffee, please.'",
            "options": ["Un café, merci", "Un thé, s'il vous plaît", "Un café, s'il vous plaît", "Une bière, merci"],
            "correctAnswer": "Un café, s'il vous plaît",
            "difficulty": "A1"
        },
        {
            "id": 3,
            "question": "Which word means 'The car'?",
            "options": ["Le train", "La maison", "La voiture", "Le vélo"],
            "correctAnswer": "La voiture",
            "difficulty": "A1"
        },
        {
            "id": 4,
            "question": "Conjugate 'être' (to be) for 'Je' (I).",
            "options": ["sois", "es", "est", "suis"],
            "correctAnswer": "suis",
            "difficulty": "A1"
        },
        {
            "id": 5,
            "question": "What is the past tense of 'manger' (to eat) in 'J'ai ___'?",
            "options": ["mangé", "manger", "mangeais", "mangs"],
            "correctAnswer": "mangé",
            "difficulty": "A2"
        },
        {
            "id": 6,
            "question": "Translate: 'I went to the cinema yesterday.'",
            "options": ["Je vais au cinéma hier", "Je suis allé au cinéma hier", "J'ai allé au cinéma hier", "Je aller au cinéma hier"],
            "correctAnswer": "Je suis allé au cinéma hier",
            "difficulty": "A2"
        },
        {
            "id": 7,
            "question": "Choose the correct form: 'Elle est ___ (happy).'",
            "options": ["heureux", "heureuse", "heureuses", "heureuxs"],
            "correctAnswer": "heureuse",
            "difficulty": "A2"
        },
        {
            "id": 8,
            "question": "'Il faut que je ___ (go).' (Subjunctive)",
            "options": ["vais", "aller", "aille", "suis allé"],
            "correctAnswer": "aille",
            "difficulty": "B1"
        },
        {
            "id": 9,
            "question": "Translate: 'If I had money, I would travel.'",
            "options": ["Si j'ai de l'argent, je voyagerai", "Si j'avais de l'argent, je voyagerais", "Si j'aurais de l'argent, je voyagerais", "Si j'avais de l'argent, je voyagerai"],
            "correctAnswer": "Si j'avais de l'argent, je voyagerais",
            "difficulty": "B1"
        },
        {
            "id": 10,
            "question": "What does 'Jeter l'éponge' mean?",
            "options": ["To clean the sponge", "To throw the sponge", "To give up", "To get angry"],
            "correctAnswer": "To give up",
            "difficulty": "B2"
        }
    ]
    
    return {"questions": questions}

@router.get("/students/check", response_model=OnboardingStatus)
async def check_onboarding(
    user_id: str = Query(..., description="Clerk User ID")
):
    """
    Check if a user has completed student onboarding.
    Returns { isComplete: bool, studentId: str | None }
    """
    try:
        collection = get_collection("students")
        doc = await collection.find_one({"clerkUserId": user_id})

        if doc:
            return {
                "isComplete": True,
                "studentId": doc["studentId"],
                "role": doc.get("role", "student")
            }
        else:
            return {
                "isComplete": False,
                "studentId": None,
                "role": None
            }

    except Exception as e:
        logger.exception(f"Failed to check onboarding | userId={user_id}")
        # Default to false in case of error to be safe, or raise 500
        raise HTTPException(status_code=500, detail=str(e))
