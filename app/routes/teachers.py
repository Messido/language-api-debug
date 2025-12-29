"""
Teacher Profile API endpoints.
Handles creation and retrieval of teacher profiles.
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

class TeacherExperience(BaseModel):
    years: int
    studentsTaught: int
    hoursTaught: int

class TeacherProfileCreate(BaseModel):
    clerkUserId: str
    teachingLanguages: List[str]
    instructionLanguage: str
    experience: TeacherExperience

class TeacherProfileResponse(BaseModel):
    id: str  # MongoDB _id
    clerkUserId: str
    teacherId: str  # T-123456
    teachingLanguages: List[str]
    instructionLanguage: str
    experience: TeacherExperience
    createdAt: datetime
    updatedAt: datetime
    role: str = "teacher"

class TeacherOnboardingStatus(BaseModel):
    isComplete: bool
    teacherId: Optional[str] = None
    role: Optional[str] = None

# --- Helper Functions ---

def generate_teacher_id() -> str:
    """Generate a random Teacher ID starting with T-."""
    # Generate 6 random digits
    digits = random.randint(100000, 999999)
    return f"T-{digits}"

def doc_to_response(doc: dict) -> dict:
    """Convert MongoDB document to API response."""
    return {
        "id": str(doc["_id"]),
        "clerkUserId": doc["clerkUserId"],
        "teacherId": doc["teacherId"],
        "teachingLanguages": doc["teachingLanguages"],
        "instructionLanguage": doc["instructionLanguage"],
        "experience": doc["experience"],
        "createdAt": doc["createdAt"],
        "updatedAt": doc.get("updatedAt", doc["createdAt"]),
        "role": doc.get("role", "teacher")
    }

# --- Routes ---

@router.post("/teachers", response_model=TeacherProfileResponse)
async def create_teacher_profile(profile: TeacherProfileCreate):
    """
    Create a new teacher profile after onboarding.
    Auto-generates a Teacher ID (T-xxxxxx).
    """
    logger.info(f"Creating teacher profile | userId={profile.clerkUserId}")

    try:
        collection = get_collection("teachers")

        # Check if profile already exists
        existing = await collection.find_one({"clerkUserId": profile.clerkUserId})
        if existing:
            logger.info(f"Teacher profile already exists | userId={profile.clerkUserId}")
            return doc_to_response(existing)

        # Generate unique Teacher ID
        teacher_id = generate_teacher_id()

        # Create document
        doc = {
            "clerkUserId": profile.clerkUserId,
            "teacherId": teacher_id,
            "teachingLanguages": profile.teachingLanguages,
            "instructionLanguage": profile.instructionLanguage,
            "experience": profile.experience.model_dump(),
            "role": "teacher",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }

        result = await collection.insert_one(doc)
        doc["_id"] = result.inserted_id

        logger.info(f"Teacher profile created | userId={profile.clerkUserId}, teacherId={teacher_id}")
        return doc_to_response(doc)

    except Exception as e:
        logger.exception(f"Failed to create teacher profile | userId={profile.clerkUserId}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teachers/me", response_model=TeacherProfileResponse)
async def get_my_teacher_profile(
    user_id: str = Query(..., description="Clerk User ID")
):
    """Get current user's teacher profile."""
    logger.info(f"Fetching teacher profile | userId={user_id}")

    try:
        collection = get_collection("teachers")
        doc = await collection.find_one({"clerkUserId": user_id})

        if not doc:
            raise HTTPException(status_code=404, detail="Profile not found")

        return doc_to_response(doc)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to fetch teacher profile | userId={user_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teachers/check", response_model=TeacherOnboardingStatus)
async def check_teacher_onboarding(
    user_id: str = Query(..., description="Clerk User ID")
):
    """
    Check if a user has completed teacher onboarding.
    Returns { isComplete: bool, teacherId: str | None }
    """
    try:
        collection = get_collection("teachers")
        doc = await collection.find_one({"clerkUserId": user_id})

        if doc:
            return {
                "isComplete": True,
                "teacherId": doc["teacherId"],
                "role": doc.get("role", "teacher")
            }
        else:
            return {
                "isComplete": False,
                "teacherId": None,
                "role": None
            }

    except Exception as e:
        logger.exception(f"Failed to check teacher onboarding | userId={user_id}")
        raise HTTPException(status_code=500, detail=str(e))
