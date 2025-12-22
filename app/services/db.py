"""
MongoDB connection module using Motor (async driver).
"""

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os

from app.core.logging import get_logger

logger = get_logger(__name__)


class MongoDB:
    """MongoDB connection manager."""
    client: Optional[AsyncIOMotorClient] = None
    db = None


mongodb = MongoDB()


async def connect_to_mongodb():
    """Connect to MongoDB Atlas."""
    mongodb_url = os.getenv("MONGODB_URL")
    database_name = os.getenv("DATABASE_NAME", "language_app")
    
    if not mongodb_url:
        logger.error("MONGODB_URL environment variable is not set")
        raise ValueError("MONGODB_URL environment variable is required")
    
    try:
        mongodb.client = AsyncIOMotorClient(mongodb_url)
        mongodb.db = mongodb.client[database_name]
        
        # Verify connection by pinging the server
        await mongodb.client.admin.command('ping')
        logger.info(f"📦 Connected to MongoDB database: {database_name}")
        
    except Exception as e:
        logger.exception(f"Failed to connect to MongoDB: {str(e)}")
        raise


async def close_mongodb_connection():
    """Close MongoDB connection."""
    if mongodb.client:
        mongodb.client.close()
        logger.info("📦 Disconnected from MongoDB")


def get_database():
    """Get the database instance."""
    if mongodb.db is None:
        raise RuntimeError("MongoDB is not connected. Call connect_to_mongodb() first.")
    return mongodb.db


def get_collection(collection_name: str):
    """Get a collection from the database."""
    db = get_database()
    return db[collection_name]
