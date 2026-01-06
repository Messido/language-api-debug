"""
Student-Teacher Relationship API endpoints.
Handles linking students to teachers and retrieving connected users.
"""

# ... (imports)
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

class RelationshipStatusUpdate(BaseModel):
    status: str  # active, rejected

class RelationshipResponse(BaseModel):
    id: str
    studentId: str
    teacherId: str
    studentClerkId: str
    teacherClerkId: str
    createdAt: datetime
    status: str = "active"  # pending, active, rejected, archived

class ConnectedStudent(BaseModel):
    id: str # Relationship ID
    studentId: str
    clerkUserId: str
    name: Optional[str] = None # In a real app, we'd fetch this from Clerk or Student Profile
    level: Optional[str] = None
    createdAt: datetime
    status: str

class ConnectedTeacher(BaseModel):
    id: str # Relationship ID
    teacherId: str
    clerkUserId: str
    name: Optional[str] = None
    createdAt: datetime
    status: str

# --- Helper Functions ---

def doc_to_response(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "studentId": doc["studentId"],
        "teacherId": doc["teacherId"],
        "studentClerkId": doc["studentClerkId"],
        "teacherClerkId": doc["teacherClerkId"],
        "createdAt": doc["createdAt"],
        "status": doc.get("status", "pending")
    }

# --- Routes ---

@router.post("/relationships/link", response_model=RelationshipResponse)
async def link_student_teacher(link_data: LinkRequest):
    """
    Send a connection request from a student to a teacher.
    Status starts as 'pending'.
    """
    logger.info(f"Requesting link: student {link_data.studentId} -> teacher {link_data.teacherId}")

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
            # If rejected, allow re-requesting? For now, just return existing
            return doc_to_response(existing)

        # 4. Create Link (Pending)
        doc = {
            "studentId": link_data.studentId,
            "teacherId": link_data.teacherId,
            "studentClerkId": student["clerkUserId"],
            "teacherClerkId": teacher["clerkUserId"],
            "createdAt": datetime.utcnow(),
            "status": "pending" 
        }

        result = await relationships_coll.insert_one(doc)
        doc["_id"] = result.inserted_id

        logger.info(f"Link request created: {link_data.studentId} -> {link_data.teacherId}")
        return doc_to_response(doc)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create link request")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/relationships/{relationship_id}/status", response_model=RelationshipResponse)
async def update_relationship_status(relationship_id: str, update: RelationshipStatusUpdate):
    """
    Update relationship status (e.g., approve 'active' or reject 'rejected').
    """
    logger.info(f"Updating relationship {relationship_id} status to {update.status}")

    try:
        relationships_coll = get_collection("relationships")
        
        if not ObjectId.is_valid(relationship_id):
             raise HTTPException(status_code=400, detail="Invalid relationship ID")

        result = await relationships_coll.find_one_and_update(
            {"_id": ObjectId(relationship_id)},
            {"$set": {"status": update.status}},
            return_document=True
        )

        if not result:
            raise HTTPException(status_code=404, detail="Relationship not found")

        return doc_to_response(result)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update relationship {relationship_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/relationships/teacher/{teacher_id}/students", response_model=List[ConnectedStudent])
async def get_teacher_students(
    teacher_id: str,
    status: Optional[str] = Query(None, description="Filter by status (active, pending)")
):
    """
    Get students linked to a specific teacher.
    """
    try:
        relationships_coll = get_collection("relationships")
        students_coll = get_collection("students")
        
        query = {"teacherId": teacher_id}
        if status:
            query["status"] = status
        else:
            # Default to showing all non-archived? Or just active? 
            # Let's show all if no status specified, or maybe just active.
            # For backward compatibility, if no status, maybe return active.
            # But for dashboard, we might want to see requests.
            # Let's filter by active if not specified to match previous behavior, 
            # but actually the UI might need to request 'pending'.
            pass

        cursor = relationships_coll.find(query)
        relationships = await cursor.to_list(length=None)
        
        if not relationships:
            return []
            
        student_ids = [r["studentId"] for r in relationships]
        
        students_cursor = students_coll.find({"studentId": {"$in": student_ids}})
        students = await students_cursor.to_list(length=None)
        
        # Map students by ID for easy lookup
        student_map = {s["studentId"]: s for s in students}

        result = []
        for r in relationships:
            s = student_map.get(r["studentId"])
            if s:
                result.append({
                    "id": str(r["_id"]),
                    "studentId": s["studentId"],
                    "clerkUserId": s["clerkUserId"],
                    "name": s.get("name") or "Student",
                    "level": s.get("level"),
                    "createdAt": r["createdAt"],
                    "status": r.get("status", "active")
                })
            
        return result

    except Exception as e:
        logger.exception(f"Failed to fetch students for teacher {teacher_id}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/relationships/student/{student_id}/teachers", response_model=List[ConnectedTeacher])
async def get_student_teachers(
    student_id: str,
    status: Optional[str] = Query(None, description="Filter by status (active, pending)")
):
    """
    Get teachers linked to a specific student.
    """
    try:
        relationships_coll = get_collection("relationships")
        teachers_coll = get_collection("teachers")
        
        query = {"studentId": student_id}
        if status:
            query["status"] = status
        
        cursor = relationships_coll.find(query)
        relationships = await cursor.to_list(length=None)
        
        if not relationships:
            return []
            
        teacher_ids = [r["teacherId"] for r in relationships]
        
        teachers_cursor = teachers_coll.find({"teacherId": {"$in": teacher_ids}})
        teachers = await teachers_cursor.to_list(length=None)
        
        teacher_map = {t["teacherId"]: t for t in teachers}
        
        result = []
        for r in relationships:
            t = teacher_map.get(r["teacherId"])
            if t:
                result.append({
                    "id": str(r["_id"]),
                    "teacherId": t["teacherId"],
                    "clerkUserId": t["clerkUserId"],
                    "name": "Teacher", # teachers don't have name field in previous file, assuming same pattern
                    "createdAt": r["createdAt"],
                    "status": r.get("status", "active")
                })
            
        return result

    except Exception as e:
        logger.exception(f"Failed to fetch teachers for student {student_id}")
        raise HTTPException(status_code=500, detail=str(e))
