"""
Student-Teacher Relationship API endpoints.
Handles linking students to teachers and retrieving connected users.
"""

from fastapi import APIRouter, HTTPException, Query, Body, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId

from app.core.logging import get_logger
from app.services.db import get_collection

logger = get_logger(__name__)

router = APIRouter()

# --- Pydantic Models ---

class LinkRequest(BaseModel):
    studentId: str  # S-123456
    teacherId: str  # T-123456

class RelationshipResponse(BaseModel):
    id: str
    studentId: str
    teacherId: str
    studentClerkId: str
    teacherClerkId: str
    createdAt: datetime
    status: str = "active"  # active, archived

class ConnectedStudent(BaseModel):
    studentId: str
    clerkUserId: str
    name: Optional[str] = None # In a real app, we'd fetch this from Clerk or Student Profile
    level: Optional[str] = None
    createdAt: datetime

class ConnectedTeacher(BaseModel):
    teacherId: str
    clerkUserId: str
    name: Optional[str] = None
    createdAt: datetime

# --- Helper Functions ---

def doc_to_response(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "studentId": doc["studentId"],
        "teacherId": doc["teacherId"],
        "studentClerkId": doc["studentClerkId"],
        "teacherClerkId": doc["teacherClerkId"],
        "createdAt": doc["createdAt"],
        "status": doc.get("status", "active")
    }

# --- Routes ---

@router.post("/relationships/link", response_model=RelationshipResponse)
async def link_student_teacher(link_data: LinkRequest):
    """
    Link a student to a teacher using their IDs.
    """
    logger.info(f"Linking student {link_data.studentId} to teacher {link_data.teacherId}")

    try:
        students_coll = get_collection("students")
        teachers_coll = get_collection("teachers")
        relationships_coll = get_collection("relationships")

        # 1. Verify Student exists
        student = await students_coll.find_one({"studentId": link_data.studentId})
        if not student:
            raise HTTPException(status_code=404, detail="Student ID not found")

        # 2. Verify Teacher exists
        teacher = await teachers_coll.find_one({"teacherId": link_data.teacherId})
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher ID not found")

        # 3. Check if link already exists
        existing = await relationships_coll.find_one({
            "studentId": link_data.studentId,
            "teacherId": link_data.teacherId
        })
        if existing:
            return doc_to_response(existing)

        # 4. Create Link
        doc = {
            "studentId": link_data.studentId,
            "teacherId": link_data.teacherId,
            "studentClerkId": student["clerkUserId"],
            "teacherClerkId": teacher["clerkUserId"],
            "createdAt": datetime.utcnow(),
            "status": "active"
        }

        result = await relationships_coll.insert_one(doc)
        doc["_id"] = result.inserted_id

        logger.info(f"Link created: {link_data.studentId} -> {link_data.teacherId}")
        return doc_to_response(doc)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to link student and teacher")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/relationships/teacher/{teacher_id}/students", response_model=List[ConnectedStudent])
async def get_teacher_students(teacher_id: str):
    """
    Get all students linked to a specific teacher.
    Also fetches basic student details (level, etc.)
    """
    try:
        relationships_coll = get_collection("relationships")
        students_coll = get_collection("students")
        
        # Find all active relationships for this teacher
        cursor = relationships_coll.find({"teacherId": teacher_id, "status": "active"})
        relationships = await cursor.to_list(length=None)
        
        if not relationships:
            return []
            
        student_ids = [r["studentId"] for r in relationships]
        
        # Fetch student profiles
        # In a real app, we might do an aggregation lookup, but two queries is fine for MVP
        students_cursor = students_coll.find({"studentId": {"$in": student_ids}})
        students = await students_cursor.to_list(length=None)
        
        # Map to response
        # Create a lookup map for relationship creation time
        rel_map = {r["studentId"]: r["createdAt"] for r in relationships}
        
        result = []
        for s in students:
            result.append({
                "studentId": s["studentId"],
                "clerkUserId": s["clerkUserId"],
                "name": s.get("name") or "Student",
                "level": s.get("level"),
                "createdAt": rel_map.get(s["studentId"], datetime.utcnow())
            })
            
        return result

    except Exception as e:
        logger.exception(f"Failed to fetch students for teacher {teacher_id}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/relationships/student/{student_id}/teachers", response_model=List[ConnectedTeacher])
async def get_student_teachers(student_id: str):
    """
    Get all teachers linked to a specific student.
    """
    try:
        relationships_coll = get_collection("relationships")
        teachers_coll = get_collection("teachers")
        
        cursor = relationships_coll.find({"studentId": student_id, "status": "active"})
        relationships = await cursor.to_list(length=None)
        
        if not relationships:
            return []
            
        teacher_ids = [r["teacherId"] for r in relationships]
        
        teachers_cursor = teachers_coll.find({"teacherId": {"$in": teacher_ids}})
        teachers = await teachers_cursor.to_list(length=None)
        
        rel_map = {r["teacherId"]: r["createdAt"] for r in relationships}
        
        result = []
        for t in teachers:
            result.append({
                "teacherId": t["teacherId"],
                "clerkUserId": t["clerkUserId"],
                "name": "Teacher", 
                "createdAt": rel_map.get(t["teacherId"], datetime.utcnow())
            })
            
        return result

    except Exception as e:
        logger.exception(f"Failed to fetch teachers for student {student_id}")
        raise HTTPException(status_code=500, detail=str(e))
