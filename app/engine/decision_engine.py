"""
STEP 3 — Decision Support Engine
==================================
Input  : RiskResult + Patient demographics
Output : urgency, suggested_action, doctor_type, next_steps[], estimated_wait_hours

Decision Tree
-------------
High Risk   → Immediate   → Neurosurgeon    → Emergency prep + ICU
Medium Risk → Moderate    → Neurologist     → MRI w/ contrast + specialist consult
Low Risk    → Low         → General Neuro   → 30-day follow-up or discharge
"""

from dataclasses import dataclass, field
from typing import List, Optional
from engine.risk_classifier import RiskResult, RISK_HIGH, RISK_MEDIUM, RISK_LOW
import logging

logger = logging.getLogger(__name__)

# Urgency constants
URGENCY_IMMEDIATE = "Immediate"
URGENCY_MODERATE  = "Moderate"
URGENCY_LOW       = "Low"


@dataclass
class PatientData:
    """Minimal patient context for decision making."""
    age: int
    gender: str                   # M | F | Other
    symptoms: List[str] = field(default_factory=list)
    medical_history: List[str] = field(default_factory=list)
    scan_id: Optional[str] = None


@dataclass
class DecisionResult:
    urgency: str                  # Immediate | Moderate | Low
    doctor_type: str              # Specialist recommended
    suggested_action: str         # Primary action summary
    next_steps: List[str]         # Ordered action plan
    estimated_wait_hours: float   # Hours until first intervention
    alert_er: bool                # Flag: notify emergency room?
    notes: str                    # Clinical notes


def make_decision(risk: RiskResult, patient: PatientData) -> DecisionResult:
    """
    Combines risk level with patient context to produce clinical decisions.

    Priority modifiers:
      - Age > 65          → escalate urgency by one tier
      - Seizure symptom   → escalate if Medium risk
      - Pediatric (< 18)  → always consult pediatric neurology
    """
    risk_level    = risk.risk_level
    age_modifier  = _age_escalation(patient.age, risk_level)
    has_seizures  = "seizures" in [s.lower() for s in patient.symptoms]

    # ── High Risk ──────────────────────────────────────────────────────────────
    if risk_level == RISK_HIGH or age_modifier == "escalate_to_high":
        return DecisionResult(
            urgency=URGENCY_IMMEDIATE,
            doctor_type="Neurosurgeon (Senior)",
            suggested_action="Emergency neurosurgical assessment and ICU admission.",
            next_steps=[
                "Activate emergency protocol immediately",
                "Transfer patient to ICU",
                "Order contrast-enhanced MRI within 2 hours",
                "Alert on-call neurosurgeon",
                "Initiate IV corticosteroids to reduce cerebral edema",
                "Consent for possible surgical intervention",
                "Notify next-of-kin",
            ],
            estimated_wait_hours=0.5,
            alert_er=True,
            notes=(
                f"High-risk tumor detected (confidence {risk.risk_probability:.0%}). "
                f"Patient age {patient.age}. Immediate action required."
            ),
        )

    # ── Medium Risk ────────────────────────────────────────────────────────────
    elif risk_level == RISK_MEDIUM:
        urgency = URGENCY_IMMEDIATE if has_seizures else URGENCY_MODERATE
        return DecisionResult(
            urgency=urgency,
            doctor_type="Neurologist" if not has_seizures else "Epileptologist + Neurologist",
            suggested_action="Specialist consult within 24 h; enhanced imaging required.",
            next_steps=[
                "Schedule MRI with gadolinium contrast within 24 hours",
                "Refer to neurology outpatient (urgent slot)",
                "Perform full neurological examination",
                "Order blood panel: CBC, CMP, coagulation",
                "Restrict strenuous activity",
                "Prescribe anti-edema medication if indicated",
                "Patient education: warning signs to watch for",
            ],
            estimated_wait_hours=4.0 if has_seizures else 24.0,
            alert_er=has_seizures,
            notes=(
                f"Medium-risk finding. Seizure history: {has_seizures}. "
                f"Urgency adjusted accordingly."
            ),
        )

    # ── Low Risk ───────────────────────────────────────────────────────────────
    else:
        # No tumor OR very low confidence small tumor
        pediatric = patient.age < 18
        return DecisionResult(
            urgency=URGENCY_LOW,
            doctor_type="Pediatric Neurologist" if pediatric else "General Neurologist",
            suggested_action="Routine follow-up; no immediate intervention required.",
            next_steps=[
                "Schedule routine MRI follow-up in 30 days",
                "General neurology outpatient appointment",
                "Lifestyle advice: sleep hygiene, stress management",
                "Patient to return immediately if headaches worsen",
                "Re-evaluate if new symptoms emerge",
            ],
            estimated_wait_hours=72.0,
            alert_er=False,
            notes=(
                f"Low-risk or no tumor detected. "
                f"{'Pediatric protocol applied.' if pediatric else 'Standard adult pathway.'}"
            ),
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _age_escalation(age: int, current_risk: str) -> str:
    """
    Older patients (≥65) with Medium risk are escalated to High-risk protocol.
    """
    if age >= 65 and current_risk == RISK_MEDIUM:
        logger.info("Age modifier: patient ≥65, escalating from Medium to High protocol")
        return "escalate_to_high"
    return "none"
