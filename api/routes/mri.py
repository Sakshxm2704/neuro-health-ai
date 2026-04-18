"""
STEP 5a — API Route: POST /upload-mri
=======================================
Accepts an MRI image upload, runs CNN inference, classifies risk,
makes a clinical decision, allocates resources, and persists everything.

Returns a unified response with scan_id for downstream polling.
"""

import uuid
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from dataclasses import asdict

from ai.preprocessing.image_processor import preprocess_image, estimate_tumor_size
from ai.model.model_loader import predict_image
from engine.risk_classifier import classify_risk
from engine.decision_engine import make_decision, PatientData
from resources.allocator import allocate_resources
from database.repository import ScanRepository, DecisionRepository, AllocationRepository
from config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()
router   = APIRouter()


# ── Response Schema ────────────────────────────────────────────────────────────
class MRIUploadResponse(BaseModel):
    scan_id: str
    status: str
    tumor_detected: bool
    confidence: float
    risk_level: str
    risk_probability: float
    urgency: str
    doctor_type: str
    suggested_action: str
    next_steps: List[str]
    icu_bed_assigned: bool
    doctor_assigned: bool
    ot_room_assigned: bool
    resource_message: str
    message: str


# ── Endpoint ───────────────────────────────────────────────────────────────────
@router.post(
    "/upload-mri",
    response_model=MRIUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload MRI scan for AI analysis",
    description=(
        "Accepts a grayscale or color MRI image (JPEG/PNG). "
        "Runs CNN inference → risk classification → decision engine → resource allocation. "
        "Returns a comprehensive clinical response."
    ),
)
async def upload_mri(
    file: UploadFile = File(..., description="MRI image file (JPEG/PNG)"),
    patient_age: int = Form(45, description="Patient age"),
    patient_gender: str = Form("M", description="Patient gender (M/F/Other)"),
    symptoms: Optional[str] = Form(
        "", description="Comma-separated symptoms e.g. 'headache,seizures'"
    ),
    medical_history: Optional[str] = Form(
        "", description="Comma-separated history e.g. 'hypertension'"
    ),
):
    # ── Validate file type ─────────────────────────────────────────────────────
    allowed_types = {"image/jpeg", "image/png", "image/jpg"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{file.content_type}'. Upload JPEG or PNG MRI images.",
        )

    scan_id = f"SCAN-{uuid.uuid4().hex[:10].upper()}"
    logger.info("📥 New MRI upload: scan_id=%s, file=%s", scan_id, file.filename)

    try:
        # ── Step 1: Read + preprocess image ───────────────────────────────────
        image_bytes = await file.read()
        image_tensor = preprocess_image(image_bytes, target_size=settings.image_size)

        # ── Step 1b: Run CNN inference ─────────────────────────────────────────
        prediction = predict_image(image_tensor, settings.model_path)
        tumor_size = estimate_tumor_size(prediction["raw_score"])

        # ── Step 2: Risk classification ────────────────────────────────────────
        risk = classify_risk(
            tumor_detected=prediction["tumor_detected"],
            confidence=prediction["confidence"],
            tumor_size=tumor_size,
        )

        # ── Step 3: Decision engine ────────────────────────────────────────────
        symptom_list = [s.strip() for s in symptoms.split(",") if s.strip()]
        history_list = [h.strip() for h in medical_history.split(",") if h.strip()]

        patient = PatientData(
            age=patient_age,
            gender=patient_gender,
            symptoms=symptom_list,
            medical_history=history_list,
            scan_id=scan_id,
        )
        decision = make_decision(risk, patient)

        # ── Step 4: Resource allocation ────────────────────────────────────────
        allocation = await allocate_resources(scan_id, risk.risk_level)

        # ── Persist to MongoDB ─────────────────────────────────────────────────
        scan_doc = {
            "scan_id": scan_id,
            "filename": file.filename,
            "patient_age": patient_age,
            "patient_gender": patient_gender,
            "symptoms": symptom_list,
            "medical_history": history_list,
            "tumor_detected": prediction["tumor_detected"],
            "confidence": prediction["confidence"],
            "raw_score": prediction["raw_score"],
            "tumor_size": tumor_size,
            "risk_level": risk.risk_level,
            "risk_probability": risk.risk_probability,
            "risk_rationale": risk.rationale,
        }

        decision_doc = {
            "scan_id": scan_id,
            **asdict(decision),
        }

        allocation_doc = {
            "scan_id": scan_id,
            **asdict(allocation),
        }

        await ScanRepository.save_scan(scan_doc)
        await DecisionRepository.save_decision(decision_doc)
        await AllocationRepository.save_allocation(allocation_doc)

        logger.info("✅ Scan %s processed: risk=%s, urgency=%s",
                    scan_id, risk.risk_level, decision.urgency)

        return MRIUploadResponse(
            scan_id=scan_id,
            status="analyzed",
            tumor_detected=prediction["tumor_detected"],
            confidence=prediction["confidence"],
            risk_level=risk.risk_level,
            risk_probability=risk.risk_probability,
            urgency=decision.urgency,
            doctor_type=decision.doctor_type,
            suggested_action=decision.suggested_action,
            next_steps=decision.next_steps,
            icu_bed_assigned=allocation.icu_bed_assigned,
            doctor_assigned=allocation.doctor_assigned,
            ot_room_assigned=allocation.ot_room_assigned,
            resource_message=allocation.message,
            message=(
                f"Scan '{file.filename}' analyzed successfully. "
                f"Tumor {'detected' if prediction['tumor_detected'] else 'not detected'}. "
                f"Risk: {risk.risk_level}. Action: {decision.urgency}."
            ),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error processing scan %s: %s", scan_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during MRI analysis.")
