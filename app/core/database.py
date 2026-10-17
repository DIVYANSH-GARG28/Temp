import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
from app.core.config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

db_manager = DatabaseManager()

async def connect_to_mongo():
    logger.info("Connecting to MongoDB at %s", settings.MONGODB_URI)
    db_manager.client = AsyncIOMotorClient(settings.MONGODB_URI)
    db_manager.db = db_manager.client[settings.MONGODB_DATABASE]
    await init_db_indexes(db_manager.db)
    logger.info("MongoDB connected successfully and indexes initialized.")

async def close_mongo_connection():
    logger.info("Closing MongoDB connection.")
    if db_manager.client:
        db_manager.client.close()
        logger.info("MongoDB connection closed.")

def get_database() -> AsyncIOMotorDatabase:
    if db_manager.db is None:
        raise RuntimeError("Database is not initialized. Please call connect_to_mongo() first.")
    return db_manager.db

def set_test_database(db: AsyncIOMotorDatabase):
    """Allow test runner to inject an async mock database (e.g. mongomock-motor)."""
    db_manager.db = db

async def init_db_indexes(db: AsyncIOMotorDatabase):
    try:
        # Users collection indexes
        await db.users.create_index([("email", ASCENDING)], unique=True)
        await db.users.create_index([("telegram_chat_id", ASCENDING)], sparse=True)

        # Profiles collection indexes
        await db.profiles.create_index([("user_id", ASCENDING)], unique=True)
        await db.profiles.create_index([("role", ASCENDING)])
        await db.profiles.create_index([("skills", ASCENDING)])

        # Mentorship requests indexes
        await db.mentorship_requests.create_index([("student_id", ASCENDING)])
        await db.mentorship_requests.create_index([("mentor_id", ASCENDING)])
        await db.mentorship_requests.create_index([("status", ASCENDING), ("deadline", ASCENDING)])

        # Meeting proposals indexes
        await db.meeting_proposals.create_index([("mentorship_request_id", ASCENDING)])
        await db.meeting_proposals.create_index([("status", ASCENDING)])

        # Telegram linking token indexes (TTL index)
        await db.telegram_links.create_index([("token", ASCENDING)], unique=True)
        await db.telegram_links.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)

        # Telegram updates deduplication
        await db.telegram_updates.create_index([("update_id", ASCENDING)], unique=True)

        # Opportunities indexes
        await db.opportunities.create_index([("type", ASCENDING)])
        await db.opportunities.create_index([("is_active", ASCENDING)])
        await db.opportunities.create_index([("creator_id", ASCENDING)])

        # Research projects indexes
        await db.research_projects.create_index([("faculty_id", ASCENDING)])
        await db.research_projects.create_index([("research_area", ASCENDING)])

        # Notifications indexes
        await db.notifications.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
        logger.info("All MongoDB indexes initialized successfully.")
    except Exception as e:
        logger.warning("Error initializing indexes (might be mock DB in tests): %s", e)
