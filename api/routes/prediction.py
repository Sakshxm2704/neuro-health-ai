"""
STEP 5b — API Route: GET /prediction/{scan_id}
===============================================
Returns stored prediction results for a given scan.
Useful for async polling after upload.
"""

import logging
from fastapi import APIRouter, HTTPException, status, Path
from pydantic import BaseModel
from typing import Optional

from database.repository import ScanRepository

logger = logging.getLogger(__name__)
router = APIRouter()


class PredictionResponse(BaseModel):
    scan_id: str
    filename: str
    tumor_detected: bool
    confidence: float
    raw_score: float
    tumor_size: str
    risk_level: str
    risk_probability: float
    risk_rationale: str
    patient_age: int
    patient_gender: str
    symptoms: list
    created_at: str


@router.get(
    "/prediction/{scan_id}",
    response_model=PredictionResponse,
    summary="Get CNN prediction result for a scan",
    description="Retrieves the stored AI prediction and risk classification for a given scan_id.",
)
async def get_prediction(
    scan_id: str = Path(..., description="Scan ID returned from /upload-mri"),
):
    doc = await ScanRepository.get_scan(scan_id)

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No scan found with ID '{scan_id}'. "
                   f"Ensure the MRI was uploaded via POST /upload-mri.",
        )

    logger.info("Prediction retrieved for scan %s", scan_id)
    return PredictionResponse(**doc)
