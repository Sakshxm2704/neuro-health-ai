"""
STEP 5d — API Route: GET /resources
=====================================
Returns current hospital resource pool status:
  - ICU bed availability
  - Doctor availability
  - OT room availability
  - Waiting queue

Also supports DELETE /resources/release/{scan_id} to free allocated resources.
"""

import logging
from fastapi import APIRouter, HTTPException, status, Path
from pydantic import BaseModel
from typing import Optional, List

from resources.allocator import get_pool, release_resources
from database.repository import AllocationRepository

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Response Schemas ───────────────────────────────────────────────────────────
class ResourceCount(BaseModel):
    total: int
    occupied: int = 0
    available: int
    occupancy_rate: str = "0%"
    on_duty: int = 0
    in_use: int = 0


class WaitingQueue(BaseModel):
    patients_waiting: int
    queue: List[dict]


class ResourceStatusResponse(BaseModel):
    icu_beds: dict
    doctors: dict
    ot_rooms: dict
    waiting_queue: WaitingQueue
    system_alert: Optional[str] = None


class AllocationResponse(BaseModel):
    scan_id: str
    risk_level: str
    icu_bed_assigned: bool
    doctor_assigned: bool
    ot_room_assigned: bool
    doctor_id: Optional[str]
    bed_number: Optional[int]
    ot_room_number: Optional[int]
    allocation_time: str
    queue_position: Optional[int]
    message: str


# ── Endpoints ──────────────────────────────────────────────────────────────────
@router.get(
    "/resources",
    summary="Get real-time hospital resource availability",
    description=(
        "Returns live status of all ICU beds, doctors, and OT rooms. "
        "Includes occupancy rates and waiting queue."
    ),
)
async def get_resources():
    pool    = get_pool()
    summary = pool.status_summary()

    # System alert if occupancy is critical
    alert = None
    icu_occ = len(pool.allocated_beds) / pool.total_icu_beds
    if icu_occ >= 0.9:
        alert = "🚨 CRITICAL: ICU occupancy ≥90%. Activate surge capacity protocol."
    elif icu_occ >= 0.7:
        alert = "⚠️ WARNING: ICU occupancy ≥70%. Monitor closely."

    return {
        **summary,
        "system_alert": alert,
    }


@router.get(
    "/resources/allocation/{scan_id}",
    response_model=AllocationResponse,
    summary="Get resource allocation for a specific scan",
)
async def get_allocation(
    scan_id: str = Path(..., description="Scan ID to look up"),
):
    doc = await AllocationRepository.get_allocation(scan_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No allocation record found for scan '{scan_id}'.",
        )
    return AllocationResponse(**doc)


@router.delete(
    "/resources/release/{scan_id}",
    summary="Release resources allocated to a scan (patient discharged)",
    description="Frees ICU bed, doctor, and OT room back to the pool.",
)
async def release_scan_resources(
    scan_id: str = Path(..., description="Scan ID whose resources should be freed"),
):
    doc = await AllocationRepository.get_allocation(scan_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No allocation found for scan '{scan_id}'.",
        )

    await release_resources(
        scan_id=scan_id,
        bed=doc.get("bed_number"),
        doctor=doc.get("doctor_id"),
        ot=doc.get("ot_room_number"),
    )

    # Mark as released in DB
    from database.connection import get_db
    db = get_db()
    await db.allocations.update_one(
        {"scan_id": scan_id},
        {"$set": {"released": True}}
    )

    logger.info("Resources released for scan %s", scan_id)
    return {"message": f"Resources for scan '{scan_id}' successfully released.", "scan_id": scan_id}
