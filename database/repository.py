"""
Database Repository — CRUD operations for all collections.
Keeps database logic separate from API and business logic.
"""

from datetime import datetime, timezone
from typing import Optional
from database.connection import get_db
import logging

logger = logging.getLogger(__name__)


class ScanRepository:
    """Handles scan records: create, read."""

    @staticmethod
    async def save_scan(scan_data: dict) -> str:
        """Insert a new scan record. Returns inserted scan_id."""
        db = get_db()
        scan_data["created_at"] = datetime.now(timezone.utc).isoformat()
        await db.scans.insert_one(scan_data)
        return scan_data["scan_id"]

    @staticmethod
    async def get_scan(scan_id: str) -> Optional[dict]:
        """Fetch a scan by its ID."""
        db = get_db()
        doc = await db.scans.find_one({"scan_id": scan_id}, {"_id": 0})
        return doc

    @staticmethod
    async def update_scan(scan_id: str, update_data: dict):
        """Partial update on a scan document."""
        db = get_db()
        await db.scans.update_one(
            {"scan_id": scan_id},
            {"$set": {**update_data, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )


class DecisionRepository:
    """Handles decision records."""

    @staticmethod
    async def save_decision(decision_data: dict) -> None:
        db = get_db()
        decision_data["created_at"] = datetime.now(timezone.utc).isoformat()
        await db.decisions.insert_one(decision_data)

    @staticmethod
    async def get_decision(scan_id: str) -> Optional[dict]:
        db = get_db()
        return await db.decisions.find_one({"scan_id": scan_id}, {"_id": 0})


class AllocationRepository:
    """Handles resource allocation records."""

    @staticmethod
    async def save_allocation(allocation_data: dict) -> None:
        db = get_db()
        allocation_data["created_at"] = datetime.now(timezone.utc).isoformat()
        await db.allocations.insert_one(allocation_data)

    @staticmethod
    async def get_allocation(scan_id: str) -> Optional[dict]:
        db = get_db()
        return await db.allocations.find_one({"scan_id": scan_id}, {"_id": 0})

    @staticmethod
    async def get_all_active() -> list:
        """List all active allocations (not released)."""
        db = get_db()
        cursor = db.allocations.find(
            {"released": {"$ne": True}}, {"_id": 0}
        ).sort("created_at", -1).limit(50)
        return await cursor.to_list(length=50)
