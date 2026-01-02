from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from app.services.db import get_database as get_db

router = APIRouter(prefix="/groups", tags=["groups"])

# Data Models
class GroupCreate(BaseModel):
    name: str
    level: str
    schedule: Optional[str] = None
    teacherId: str

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    level: Optional[str] = None
    schedule: Optional[str] = None

class GroupResponse(BaseModel):
    id: str
    name: str
    level: str
    schedule: Optional[str] = None
    teacherId: str
    createdAt: str
    studentCount: int = 0
    students: List[str] = [] # List of Student IDs

class AddStudentsRequest(BaseModel):
    studentIds: List[str]

# --- Helper Functions (MongoDB) ---

def group_doc_to_response(doc):
    return GroupResponse(
        id=doc["groupId"],
        name=doc["name"],
        level=doc["level"],
        schedule=doc.get("schedule"),
        teacherId=doc["teacherId"],
        createdAt=doc["createdAt"],
        studentCount=len(doc.get("students", [])),
        students=doc.get("students", [])
    )

# --- Routes ---

@router.post("/", response_model=GroupResponse)
async def create_group(group: GroupCreate):
    db = get_db()
    
    # Verify teacher exists (optional but good practice)
    # For now, we trust the teacherId from the frontend/auth context
    
    group_id = f"G-{uuid.uuid4().hex[:6].upper()}"
    
    new_group = {
        "groupId": group_id,
        "name": group.name,
        "level": group.level,
        "schedule": group.schedule,
        "teacherId": group.teacherId,
        "students": [],
        "createdAt": datetime.utcnow().isoformat()
    }
    
    db.groups.insert_one(new_group)
    
    return group_doc_to_response(new_group)

@router.get("/teacher/{teacher_id}", response_model=List[GroupResponse])
@router.get("/teacher/{teacher_id}", response_model=List[GroupResponse])
async def get_teacher_groups(teacher_id: str):
    db = get_db()
    # MongoDB AsyncIOMotorCursor requires to_list for async retrieval
    groups = await db.groups.find({"teacherId": teacher_id}).to_list(length=None)
    return [group_doc_to_response(g) for g in groups]

@router.get("/{group_id}", response_model=GroupResponse)
@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(group_id: str):
    db = get_db()
    group = await db.groups.find_one({"groupId": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group_doc_to_response(group)

@router.post("/{group_id}/students", response_model=GroupResponse)
@router.post("/{group_id}/students", response_model=GroupResponse)
async def add_students_to_group(group_id: str, request: AddStudentsRequest):
    db = get_db()
    
    group = await db.groups.find_one({"groupId": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    # Verify students exist (optional but recommended)
    # for student_id in request.studentIds: ...
    
    # Add students to set to avoid duplicates
    current_students = set(group.get("students", []))
    current_students.update(request.studentIds)
    
    await db.groups.update_one(
        {"groupId": group_id},
        {"$set": {"students": list(current_students)}}
    )
    
    updated_group = await db.groups.find_one({"groupId": group_id})
    return group_doc_to_response(updated_group)

@router.delete("/{group_id}/students/{student_id}", response_model=GroupResponse)
@router.delete("/{group_id}/students/{student_id}", response_model=GroupResponse)
async def remove_student_from_group(group_id: str, student_id: str):
    db = get_db()
    
    group = await db.groups.find_one({"groupId": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    await db.groups.update_one(
        {"groupId": group_id},
        {"$pull": {"students": student_id}}
    )
    
    updated_group = await db.groups.find_one({"groupId": group_id})
    return group_doc_to_response(updated_group)

@router.delete("/{group_id}")
@router.delete("/{group_id}")
async def delete_group(group_id: str):
    db = get_db()
    result = await db.groups.delete_one({"groupId": group_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Group not found")
    return {"message": "Group deleted successfully"}
