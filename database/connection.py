"""
Database — MongoDB Connection via Motor (async)
================================================
Collections:
  scans       — raw scan metadata and prediction results
  decisions   — clinical decisions per scan
  allocations — resource allocation records
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Module-level client (initialized once)
_client: AsyncIOMotorClient = None
_db: AsyncIOMotorDatabase = None


async def init_db():
    """Connect to MongoDB and create indexes."""
    global _client, _db

    _client = AsyncIOMotorClient(settings.mongo_uri)
    _db = _client[settings.mongo_db]

    # Create indexes for fast lookup by scan_id
    await _db.scans.create_index("scan_id", unique=True)
    await _db.decisions.create_index("scan_id")
    await _db.allocations.create_index("scan_id")

    logger.info("MongoDB connected: %s / %s", settings.mongo_uri, settings.mongo_db)


def get_db() -> AsyncIOMotorDatabase:
    """Return the active database instance."""
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db


async def close_db():
    """Close the MongoDB connection gracefully."""
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed.")
