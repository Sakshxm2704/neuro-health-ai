"""
STEP 5c — API Route: GET /decision/{scan_id}
=============================================
Returns the clinical decision for a given scan.
"""

import logging
from fastapi import APIRouter, HTTPException, status, Path
from pydantic import BaseModel
from typing import List

from database.repository import DecisionRepository

logger = logging.getLogger(__name__)
router = APIRouter()


class DecisionResponse(BaseModel):
    scan_id: str
    urgency: str
    doctor_type: str
    suggested_action: str
    next_steps: List[str]
    estimated_wait_hours: float
    alert_er: bool
    notes: str
    created_at: str


@router.get(
    "/decision/{scan_id}",
    response_model=DecisionResponse,
    summary="Get clinical decision for a scan",
    description=(
        "Returns the decision engine output: urgency level, specialist type, "
        "ordered next steps, and ER alert flag."
    ),
)
async def get_decision(
    scan_id: str = Path(..., description="Scan ID returned from /upload-mri"),
):
    doc = await DecisionRepository.get_decision(scan_id)

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No decision found for scan '{scan_id}'.",
        )

    logger.info("Decision retrieved for scan %s", scan_id)
    return DecisionResponse(**doc)
