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
    logger.info("Connecting to MongoDB database: %s", settings.MONGODB_DATABASE)
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
        # Partial unique index: prevents concurrent duplicate ACTIVE requests.
        # Only applies when status='pending'; terminal statuses (accepted/declined/
        # cancelled/expired) are excluded so legitimate resubmission is never blocked.
        # NOTE: mongomock-motor does not support partialFilterExpression — this index
        # is silently skipped in unit tests but is enforced on a real MongoDB Atlas cluster.
        try:
            await db.mentorship_requests.create_index(
                [("student_id", ASCENDING), ("mentor_id", ASCENDING)],
                unique=True,
                partialFilterExpression={"status": "pending"},
                name="unique_active_mentorship_request",
            )
        except Exception as idx_err:
            logger.warning(
                "Partial unique index on mentorship_requests could not be created "
                "(may already exist, or running against mongomock which does not support "
                "partialFilterExpression): %s",
                idx_err,
            )

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

        # Mentor approval tokens — enable atomic upsert lookup and TTL-style expiry
        await db.mentor_approvals.create_index(
            [("student_id", ASCENDING), ("mentor_id", ASCENDING), ("status", ASCENDING)],
            name="mentor_approval_lookup",
        )
        await db.mentor_approvals.create_index([("expires_at", ASCENDING)], name="mentor_approval_expiry")

        # Transactional outbox events indexes
        await db.outbox_events.create_index([("event_id", ASCENDING)], unique=True)
        await db.outbox_events.create_index([("status", ASCENDING), ("created_at", ASCENDING)])
        await db.outbox_events.create_index([("status", ASCENDING), ("lease_expires_at", ASCENDING), ("next_retry_at", ASCENDING)])
        logger.info("All MongoDB indexes initialized successfully.")
    except Exception as e:

        logger.warning("Error initializing indexes (might be mock DB in tests): %s", e)
