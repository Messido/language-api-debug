import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def fix_names():
    # Connect directly to MongoDB
    # Use env var
    uri = os.getenv("MONGODB_URL")
    if not uri:
        # Fallback to local if not set, or print error
        uri = "mongodb://localhost:27017"
        print("Warning: MONGODB_URL not found in env, using localhost default.")
    
    # print(f"Connecting to {uri}") # Don't print secrets
    
    client = AsyncIOMotorClient(uri)
    db = client["language_app"]
    
    print(f"Connected to database: {db.name}")
    
    teachers = await db["teachers"].find({}).to_list(None)
    print(f"Found {len(teachers)} teachers.")
    
    for t in teachers:
        clerk_id = t.get("clerkUserId")
        current_name = t.get("name")
        
        # 1. Try to fetch from student profile
        student = await db["students"].find_one({"clerkUserId": clerk_id}) if clerk_id else None
        
        new_name = None
        
        if student and student.get("name"):
            new_name = student["name"]
        elif t.get("teacherId") == "T-808228":
             # Fallback for the main user if student profile missing (based on system user)
             new_name = "Siddharth" 
        else:
             # Neutral fallback if currently "Professor French" or missing
             if current_name == "Professor French" or not current_name:
                 new_name = "Teacher"
        
        # Update if changed
        if new_name and new_name != current_name:
            print(f"Updating {t.get('teacherId')} from '{current_name}' to '{new_name}'")
            await db["teachers"].update_one(
                {"_id": t["_id"]},
                {"$set": {"name": new_name}}
            )
            
    print("Done.")

if __name__ == "__main__":
    asyncio.run(fix_names())
