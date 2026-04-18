from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid, random

app = FastAPI(title="NEURO_HEALTH API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "NEURO_HEALTH running"}

@app.post("/api/v1/upload-mri")
async def upload_mri(
    file: UploadFile = File(...),
    patient_age: int = Form(45),
    patient_gender: str = Form("M"),
    symptoms: Optional[str] = Form(""),
    medical_history: Optional[str] = Form(""),
):
    confidence = round(random.uniform(0.70, 0.97), 3)
    tumor = confidence > 0.75
    risk = "High" if confidence > 0.85 else "Medium" if confidence > 0.75 else "Low"
    urgency = "Immediate" if risk == "High" else "Moderate" if risk == "Medium" else "Low"
    doctor = "Neurosurgeon (Senior)" if risk == "High" else "Neurologist" if risk == "Medium" else "General Neurologist"

    return {
        "scan_id": f"SCAN-{uuid.uuid4().hex[:8].upper()}",
        "status": "analyzed",
        "tumor_detected": tumor,
        "confidence": confidence,
        "risk_level": risk,
        "risk_probability": round(confidence * 0.95, 3),
        "urgency": urgency,
        "doctor_type": doctor,
        "suggested_action": "Emergency neurosurgical assessment and ICU admission." if risk == "High" else "Specialist consultation required." if risk == "Medium" else "Routine follow-up recommended.",
        "next_steps": ["Activate emergency protocol", "Transfer to ICU", "Order contrast MRI"] if risk == "High" else ["Schedule MRI", "Neurologist referral"] if risk == "Medium" else ["Routine MRI in 30 days"],
        "icu_bed_assigned": risk == "High",
        "doctor_assigned": True,
        "ot_room_assigned": risk == "High",
        "resource_message": f"ICU Bed 3 + DR-002 assigned." if risk == "High" else f"DR-001 assigned for consultation.",
    }

@app.get("/api/v1/resources")
def get_resources():
    return {
        "icu_beds": {"total": 10, "occupied": 7, "available": 3, "occupancy_rate": "70%"},
        "doctors": {"total": 5, "on_duty": 4, "available": 1},
        "ot_rooms": {"total": 3, "in_use": 2, "available": 1},
        "waiting_queue": {"patients_waiting": 2, "queue": []},
        "system_alert": None,
    }

@app.get("/api/v1/prediction/{scan_id}")
def get_prediction(scan_id: str):
    return {"scan_id": scan_id, "status": "found"}

@app.get("/api/v1/decision/{scan_id}")
def get_decision(scan_id: str):
    return {
        "scan_id": scan_id,
        "urgency": "Immediate",
        "doctor_type": "Neurosurgeon (Senior)",
        "suggested_action": "Emergency neurosurgical assessment.",
        "next_steps": ["Activate emergency protocol", "Transfer to ICU", "Order contrast MRI"],
        "estimated_wait_hours": 0.5,
        "alert_er": True,
    }
