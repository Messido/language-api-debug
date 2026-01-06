import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def check_name():
    uri = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(uri)
    db = client["language_app"]
    
    teacher = await db["teachers"].find_one({"teacherId": "T-808228"})
    if teacher:
        print(f"Teacher T-808228 Name: {teacher.get('name')}")
        print(f"Clerk ID: {teacher.get('clerkUserId')}")
    else:
        print("Teacher T-808228 not found.")

if __name__ == "__main__":
    asyncio.run(check_name())
