"""
STEP 2 — Risk Classification Engine
=====================================
Input  : tumor_detected, confidence_score, tumor_size
Output : risk_level (Low / Medium / High), risk_probability, rationale

Risk Matrix
-----------
| Tumor Size | Confidence | Risk Level |
|------------|------------|------------|
| small      | any        | Low        |
| medium     | < 0.75     | Low        |
| medium     | ≥ 0.75     | Medium     |
| large      | < 0.80     | Medium     |
| large      | ≥ 0.80     | High       |
| No tumor   | any        | Low        |
"""

from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Risk levels as constants
RISK_LOW    = "Low"
RISK_MEDIUM = "Medium"
RISK_HIGH   = "High"


@dataclass
class RiskResult:
    risk_level: str          # Low | Medium | High
    risk_probability: float  # 0.0 – 1.0
    tumor_size: str          # small | medium | large | none
    rationale: str           # Human-readable explanation


def classify_risk(
    tumor_detected: bool,
    confidence: float,
    tumor_size: str,
) -> RiskResult:
    """
    Applies the risk matrix and returns a RiskResult.

    Parameters
    ----------
    tumor_detected : bool   — CNN output (True = tumor present)
    confidence     : float  — model confidence (0–1)
    tumor_size     : str    — 'small' | 'medium' | 'large' (from heuristic)
    """

    if not tumor_detected:
        return RiskResult(
            risk_level=RISK_LOW,
            risk_probability=round(1.0 - confidence, 4),
            tumor_size="none",
            rationale="No tumor detected by CNN. Routine follow-up recommended.",
        )

    # ── Risk matrix ──────────────────────────────────────────────────────────
    if tumor_size == "small":
        level = RISK_LOW
        prob  = _scale_probability(confidence, base=0.20, cap=0.40)
        note  = "Small tumor detected with manageable confidence. Monitor closely."

    elif tumor_size == "medium":
        if confidence < 0.75:
            level = RISK_LOW
            prob  = _scale_probability(confidence, base=0.35, cap=0.55)
            note  = "Medium tumor, lower confidence. Further imaging advised."
        else:
            level = RISK_MEDIUM
            prob  = _scale_probability(confidence, base=0.55, cap=0.75)
            note  = "Medium tumor with moderate confidence. Specialist evaluation needed."

    elif tumor_size == "large":
        if confidence < 0.80:
            level = RISK_MEDIUM
            prob  = _scale_probability(confidence, base=0.60, cap=0.80)
            note  = "Large tumor suspected. Immediate specialist consultation required."
        else:
            level = RISK_HIGH
            prob  = _scale_probability(confidence, base=0.80, cap=0.99)
            note  = "Large high-confidence tumor detected. Emergency intervention likely needed."

    else:
        # Fallback for unknown size
        level = RISK_MEDIUM
        prob  = confidence
        note  = "Tumor detected; size estimation unavailable."

    logger.info("Risk classified: level=%s, prob=%.3f, size=%s",
                level, prob, tumor_size)

    return RiskResult(
        risk_level=level,
        risk_probability=round(prob, 4),
        tumor_size=tumor_size,
        rationale=note,
    )


def _scale_probability(confidence: float, base: float, cap: float) -> float:
    """
    Maps model confidence [0.5, 1.0] → [base, cap] linearly.
    Ensures risk probability reflects both model certainty and severity tier.
    """
    # confidence is in [0.5, 1.0] for positive detections
    normalized = (confidence - 0.5) / 0.5   # [0, 1]
    return base + normalized * (cap - base)
