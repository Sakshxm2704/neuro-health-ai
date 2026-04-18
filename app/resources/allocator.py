"""
STEP 4 — Resource Allocation Module
=====================================
Simulates a hospital resource pool:
  - ICU Beds    (default: 10)
  - Doctors     (default: 5)
  - OT Rooms    (default: 3)

Allocation logic:
  High Risk   → ICU bed + Doctor + OT Room (if available)
  Medium Risk → Doctor (urgent) + no ICU unless critical
  Low Risk    → Doctor (scheduled)

Thread-safe using asyncio.Lock for concurrent requests.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timezone

from engine.risk_classifier import RISK_HIGH, RISK_MEDIUM, RISK_LOW
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class ResourceAllocation:
    """Result of an allocation attempt."""
    scan_id: str
    risk_level: str
    icu_bed_assigned: bool
    doctor_assigned: bool
    ot_room_assigned: bool
    doctor_id: Optional[str]
    bed_number: Optional[int]
    ot_room_number: Optional[int]
    allocation_time: str
    queue_position: Optional[int]     # Non-None if resource unavailable
    message: str


@dataclass
class ResourcePool:
    """In-memory resource state (use Redis for multi-instance production)."""
    total_icu_beds: int
    total_doctors: int
    total_ot_rooms: int

    # Tracking allocated resources
    allocated_beds: List[int]          = field(default_factory=list)
    allocated_doctors: List[str]       = field(default_factory=list)
    allocated_ot_rooms: List[int]      = field(default_factory=list)
    waiting_queue: List[dict]          = field(default_factory=list)

    @property
    def free_beds(self) -> List[int]:
        all_beds = set(range(1, self.total_icu_beds + 1))
        return sorted(all_beds - set(self.allocated_beds))

    @property
    def free_doctors(self) -> List[str]:
        all_docs = {f"DR-{i:03d}" for i in range(1, self.total_doctors + 1)}
        return sorted(all_docs - set(self.allocated_doctors))

    @property
    def free_ot_rooms(self) -> List[int]:
        all_ots = set(range(1, self.total_ot_rooms + 1))
        return sorted(all_ots - set(self.allocated_ot_rooms))

    def status_summary(self) -> dict:
        return {
            "icu_beds": {
                "total": self.total_icu_beds,
                "occupied": len(self.allocated_beds),
                "available": len(self.free_beds),
                "occupancy_rate": f"{len(self.allocated_beds) / self.total_icu_beds:.0%}",
            },
            "doctors": {
                "total": self.total_doctors,
                "on_duty": len(self.allocated_doctors),
                "available": len(self.free_doctors),
            },
            "ot_rooms": {
                "total": self.total_ot_rooms,
                "in_use": len(self.allocated_ot_rooms),
                "available": len(self.free_ot_rooms),
            },
            "waiting_queue": {
                "patients_waiting": len(self.waiting_queue),
                "queue": self.waiting_queue,
            },
        }


# ── Singleton Pool + Lock ──────────────────────────────────────────────────────
_pool: Optional[ResourcePool] = None
_lock = asyncio.Lock()


def get_pool() -> ResourcePool:
    global _pool
    if _pool is None:
        _pool = ResourcePool(
            total_icu_beds=settings.total_icu_beds,
            total_doctors=settings.total_doctors,
            total_ot_rooms=settings.total_ot_rooms,
        )
    return _pool


# ── Allocation Logic ───────────────────────────────────────────────────────────
async def allocate_resources(scan_id: str, risk_level: str) -> ResourceAllocation:
    """
    Thread-safe resource allocation.
    High-risk patients get priority (ICU + Doctor + OT).
    """
    async with _lock:
        pool = get_pool()
        now  = datetime.now(timezone.utc).isoformat()

        if risk_level == RISK_HIGH:
            return _allocate_high(pool, scan_id, now)

        elif risk_level == RISK_MEDIUM:
            return _allocate_medium(pool, scan_id, now)

        else:  # Low risk
            return _allocate_low(pool, scan_id, now)


def _allocate_high(pool: ResourcePool, scan_id: str, now: str) -> ResourceAllocation:
    """High risk → needs ICU bed + Doctor + OT (best effort)."""
    bed    = pool.free_beds[0]    if pool.free_beds    else None
    doc    = pool.free_doctors[0] if pool.free_doctors else None
    ot     = pool.free_ot_rooms[0] if pool.free_ot_rooms else None

    if not bed or not doc:
        # Critical: queue and alert
        position = len(pool.waiting_queue) + 1
        pool.waiting_queue.append({"scan_id": scan_id, "risk": RISK_HIGH, "queued_at": now})
        logger.warning("⚠️  HIGH-RISK patient %s queued at position %d — resources exhausted",
                       scan_id, position)
        return ResourceAllocation(
            scan_id=scan_id, risk_level=RISK_HIGH,
            icu_bed_assigned=False, doctor_assigned=False, ot_room_assigned=False,
            doctor_id=None, bed_number=None, ot_room_number=None,
            allocation_time=now, queue_position=position,
            message="⚠️ All ICU resources exhausted. Patient placed in PRIORITY queue. "
                    "Escalate to hospital administrator immediately.",
        )

    # Commit allocation
    pool.allocated_beds.append(bed)
    pool.allocated_doctors.append(doc)
    if ot:
        pool.allocated_ot_rooms.append(ot)

    logger.info("✅ HIGH-RISK allocation: bed=%s, doc=%s, ot=%s", bed, doc, ot)
    return ResourceAllocation(
        scan_id=scan_id, risk_level=RISK_HIGH,
        icu_bed_assigned=True, doctor_assigned=True, ot_room_assigned=ot is not None,
        doctor_id=doc, bed_number=bed, ot_room_number=ot,
        allocation_time=now, queue_position=None,
        message=f"Emergency allocation complete. ICU Bed {bed}, {doc} assigned"
                + (f", OT Room {ot} reserved." if ot else ". No OT available — waitlisted."),
    )


def _allocate_medium(pool: ResourcePool, scan_id: str, now: str) -> ResourceAllocation:
    """Medium risk → Doctor only (no ICU unless available)."""
    doc = pool.free_doctors[0] if pool.free_doctors else None

    if not doc:
        position = len(pool.waiting_queue) + 1
        pool.waiting_queue.append({"scan_id": scan_id, "risk": RISK_MEDIUM, "queued_at": now})
        return ResourceAllocation(
            scan_id=scan_id, risk_level=RISK_MEDIUM,
            icu_bed_assigned=False, doctor_assigned=False, ot_room_assigned=False,
            doctor_id=None, bed_number=None, ot_room_number=None,
            allocation_time=now, queue_position=position,
            message=f"No doctor available. Patient queued at position {position}.",
        )

    pool.allocated_doctors.append(doc)
    return ResourceAllocation(
        scan_id=scan_id, risk_level=RISK_MEDIUM,
        icu_bed_assigned=False, doctor_assigned=True, ot_room_assigned=False,
        doctor_id=doc, bed_number=None, ot_room_number=None,
        allocation_time=now, queue_position=None,
        message=f"{doc} assigned for specialist consultation. ICU not required at this stage.",
    )


def _allocate_low(pool: ResourcePool, scan_id: str, now: str) -> ResourceAllocation:
    """Low risk → schedule a doctor; no emergency resources."""
    doc = pool.free_doctors[0] if pool.free_doctors else None

    if doc:
        pool.allocated_doctors.append(doc)

    return ResourceAllocation(
        scan_id=scan_id, risk_level=RISK_LOW,
        icu_bed_assigned=False, doctor_assigned=doc is not None, ot_room_assigned=False,
        doctor_id=doc, bed_number=None, ot_room_number=None,
        allocation_time=now, queue_position=None,
        message=(
            f"{doc} scheduled for routine consultation."
            if doc else
            "All doctors busy. Appointment will be booked for next available slot."
        ),
    )


async def release_resources(scan_id: str, bed: int = None,
                            doctor: str = None, ot: int = None):
    """Release previously allocated resources back to the pool."""
    async with _lock:
        pool = get_pool()
        if bed    and bed    in pool.allocated_beds:     pool.allocated_beds.remove(bed)
        if doctor and doctor in pool.allocated_doctors:  pool.allocated_doctors.remove(doctor)
        if ot     and ot     in pool.allocated_ot_rooms: pool.allocated_ot_rooms.remove(ot)
        logger.info("Resources released for scan %s", scan_id)
