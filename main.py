from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uuid
import numpy as np
from PIL import Image
import io
import pickle
import os

app = FastAPI(title="NEURO_HEALTH API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = os.path.join("ai", "model", "brain_tumor_model.pkl")
model = None

def load_model():
    global model
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        print("Model loaded!")
    else:
        print("Model not found!")

load_model()

def preprocess(image_bytes, size=64):
    img = Image.open(io.BytesIO(image_bytes)).convert("L")
    img = img.resize((size, size))
    arr = np.array(img, dtype=np.float32) / 255.0
    return arr.flatten().reshape(1, -1)

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
    image_bytes = await file.read()
    features = preprocess(image_bytes)

    if model:
        proba = model.predict_proba(features)[0]
        tumor_prob = float(proba[1])
        tumor_detected = tumor_prob >= 0.3
        confidence = round(tumor_prob if tumor_detected else 1 - tumor_prob, 3)
    else:
        tumor_detected = False
        confidence = 0.5
        tumor_prob = 0.5

    if tumor_prob >= 0.4:
        risk = "High"
        urgency = "Immediate"
        doctor = "Neurosurgeon (Senior)"
        action = "Emergency neurosurgical assessment and ICU admission."
        steps = ["Activate emergency protocol", "Transfer to ICU", "Order contrast MRI", "Alert neurosurgeon"]
        icu = True
        ot = True
    elif tumor_prob >= 0.3:
        risk = "Medium"
        urgency = "Moderate"
        doctor = "Neurologist"
        action = "Specialist consultation within 24 hours required."
        steps = ["Schedule MRI with contrast", "Neurologist referral", "Blood panel"]
        icu = False
        ot = False
    else:
        risk = "Low"
        urgency = "Low"
        doctor = "General Neurologist"
        action = "Routine follow-up recommended."
        steps = ["Schedule routine MRI in 30 days", "General neurology appointment"]
        icu = False
        ot = False

    return {
        "scan_id": f"SCAN-{uuid.uuid4().hex[:8].upper()}",
        "status": "analyzed",
        "tumor_detected": tumor_detected,
        "confidence": confidence,
        "risk_level": risk,
        "risk_probability": round(tumor_prob, 3),
        "urgency": urgency,
        "doctor_type": doctor,
        "suggested_action": action,
        "next_steps": steps,
        "icu_bed_assigned": icu,
        "doctor_assigned": True,
        "ot_room_assigned": ot,
        "resource_message": f"ICU Bed 3 + DR-002 assigned." if icu else "DR-001 assigned for consultation.",
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
        "next_steps": ["Activate emergency protocol", "Transfer to ICU"],
        "estimated_wait_hours": 0.5,
        "alert_er": True,
    }
