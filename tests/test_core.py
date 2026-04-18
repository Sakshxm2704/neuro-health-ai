"""
Test Suite — Neuro Health Ecosystem
=====================================
Tests all core modules without requiring a live MongoDB or model file.
Run with:  pytest tests/ -v
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Risk Classifier Tests ──────────────────────────────────────────────────────
class TestRiskClassifier:
    from engine.risk_classifier import classify_risk, RISK_LOW, RISK_MEDIUM, RISK_HIGH

    def test_no_tumor_is_low_risk(self):
        from engine.risk_classifier import classify_risk, RISK_LOW
        result = classify_risk(tumor_detected=False, confidence=0.95, tumor_size="none")
        assert result.risk_level == RISK_LOW
        assert result.tumor_size == "none"

    def test_small_tumor_low_risk(self):
        from engine.risk_classifier import classify_risk, RISK_LOW
        result = classify_risk(tumor_detected=True, confidence=0.82, tumor_size="small")
        assert result.risk_level == RISK_LOW

    def test_medium_tumor_high_conf_medium_risk(self):
        from engine.risk_classifier import classify_risk, RISK_MEDIUM
        result = classify_risk(tumor_detected=True, confidence=0.85, tumor_size="medium")
        assert result.risk_level == RISK_MEDIUM

    def test_large_tumor_high_conf_high_risk(self):
        from engine.risk_classifier import classify_risk, RISK_HIGH
        result = classify_risk(tumor_detected=True, confidence=0.92, tumor_size="large")
        assert result.risk_level == RISK_HIGH

    def test_large_tumor_low_conf_medium_risk(self):
        from engine.risk_classifier import classify_risk, RISK_MEDIUM
        result = classify_risk(tumor_detected=True, confidence=0.62, tumor_size="large")
        assert result.risk_level == RISK_MEDIUM

    def test_probability_in_range(self):
        from engine.risk_classifier import classify_risk
        result = classify_risk(tumor_detected=True, confidence=0.9, tumor_size="large")
        assert 0.0 <= result.risk_probability <= 1.0

    def test_rationale_not_empty(self):
        from engine.risk_classifier import classify_risk
        result = classify_risk(tumor_detected=True, confidence=0.7, tumor_size="medium")
        assert len(result.rationale) > 0


# ── Decision Engine Tests ──────────────────────────────────────────────────────
class TestDecisionEngine:

    def _make_risk(self, level, prob=0.8, size="large"):
        from engine.risk_classifier import RiskResult
        return RiskResult(
            risk_level=level,
            risk_probability=prob,
            tumor_size=size,
            rationale="Test rationale",
        )

    def _make_patient(self, age=40, symptoms=None):
        from engine.decision_engine import PatientData
        return PatientData(age=age, gender="M", symptoms=symptoms or [])

    def test_high_risk_is_immediate(self):
        from engine.decision_engine import make_decision
        from engine.risk_classifier import RISK_HIGH
        decision = make_decision(self._make_risk(RISK_HIGH), self._make_patient())
        assert decision.urgency == "Immediate"
        assert decision.alert_er is True

    def test_medium_risk_moderate_urgency(self):
        from engine.decision_engine import make_decision
        from engine.risk_classifier import RISK_MEDIUM
        decision = make_decision(self._make_risk(RISK_MEDIUM), self._make_patient())
        assert decision.urgency == "Moderate"

    def test_low_risk_low_urgency(self):
        from engine.decision_engine import make_decision
        from engine.risk_classifier import RISK_LOW
        decision = make_decision(self._make_risk(RISK_LOW, size="none"), self._make_patient())
        assert decision.urgency == "Low"
        assert decision.alert_er is False

    def test_medium_with_seizures_escalates(self):
        from engine.decision_engine import make_decision
        from engine.risk_classifier import RISK_MEDIUM
        decision = make_decision(
            self._make_risk(RISK_MEDIUM),
            self._make_patient(symptoms=["seizures"])
        )
        assert decision.urgency == "Immediate"

    def test_elderly_medium_escalates_to_immediate(self):
        from engine.decision_engine import make_decision
        from engine.risk_classifier import RISK_MEDIUM
        decision = make_decision(
            self._make_risk(RISK_MEDIUM),
            self._make_patient(age=70)  # ≥65 → escalate
        )
        assert decision.urgency == "Immediate"

    def test_pediatric_gets_specialist(self):
        from engine.decision_engine import make_decision
        from engine.risk_classifier import RISK_LOW
        decision = make_decision(
            self._make_risk(RISK_LOW, size="none"),
            self._make_patient(age=12)
        )
        assert "Pediatric" in decision.doctor_type

    def test_next_steps_not_empty(self):
        from engine.decision_engine import make_decision
        from engine.risk_classifier import RISK_HIGH
        decision = make_decision(self._make_risk(RISK_HIGH), self._make_patient())
        assert len(decision.next_steps) >= 3


# ── Image Preprocessing Tests ──────────────────────────────────────────────────
class TestPreprocessing:

    def _make_dummy_jpeg(self) -> bytes:
        """Create a minimal valid JPEG in memory."""
        from PIL import Image
        import io
        img = Image.fromarray(np.zeros((64, 64), dtype=np.uint8), mode="L")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()

    def test_output_shape(self):
        from ai.preprocessing.image_processor import preprocess_image
        arr = preprocess_image(self._make_dummy_jpeg(), target_size=128)
        assert arr.shape == (1, 128, 128, 1)

    def test_pixel_range(self):
        from ai.preprocessing.image_processor import preprocess_image
        arr = preprocess_image(self._make_dummy_jpeg(), target_size=128)
        assert arr.min() >= 0.0
        assert arr.max() <= 1.0

    def test_invalid_bytes_raises(self):
        from ai.preprocessing.image_processor import preprocess_image
        with pytest.raises(ValueError):
            preprocess_image(b"not-an-image", target_size=128)

    def test_tumor_size_thresholds(self):
        from ai.preprocessing.image_processor import estimate_tumor_size
        assert estimate_tumor_size(0.55) == "small"
        assert estimate_tumor_size(0.70) == "medium"
        assert estimate_tumor_size(0.90) == "large"


# ── Resource Allocator Tests ───────────────────────────────────────────────────
class TestResourceAllocator:

    def _fresh_pool(self):
        """Reset pool for isolated tests."""
        from resources.allocator import ResourcePool
        return ResourcePool(total_icu_beds=3, total_doctors=2, total_ot_rooms=1)

    def test_free_beds_all_available(self):
        pool = self._fresh_pool()
        assert len(pool.free_beds) == 3

    def test_allocated_reduces_free(self):
        pool = self._fresh_pool()
        pool.allocated_beds.append(1)
        assert len(pool.free_beds) == 2
        assert 1 not in pool.free_beds

    def test_free_doctors_available(self):
        pool = self._fresh_pool()
        assert len(pool.free_doctors) == 2

    def test_status_summary_keys(self):
        pool = self._fresh_pool()
        summary = pool.status_summary()
        assert "icu_beds" in summary
        assert "doctors" in summary
        assert "ot_rooms" in summary
        assert "waiting_queue" in summary

    @pytest.mark.asyncio
    async def test_high_risk_allocation(self):
        import resources.allocator as alloc_module
        # Inject fresh pool for test isolation
        alloc_module._pool = alloc_module.ResourcePool(
            total_icu_beds=5, total_doctors=3, total_ot_rooms=2
        )
        result = await alloc_module.allocate_resources("SCAN-TEST-HIGH", "High")
        assert result.icu_bed_assigned is True
        assert result.doctor_assigned is True

    @pytest.mark.asyncio
    async def test_low_risk_no_icu(self):
        import resources.allocator as alloc_module
        alloc_module._pool = alloc_module.ResourcePool(
            total_icu_beds=5, total_doctors=3, total_ot_rooms=2
        )
        result = await alloc_module.allocate_resources("SCAN-TEST-LOW", "Low")
        assert result.icu_bed_assigned is False

    @pytest.mark.asyncio
    async def test_exhausted_resources_queues_patient(self):
        import resources.allocator as alloc_module
        # Fill all resources
        pool = alloc_module.ResourcePool(
            total_icu_beds=1, total_doctors=1, total_ot_rooms=1
        )
        pool.allocated_beds  = [1]
        pool.allocated_doctors = ["DR-001"]
        alloc_module._pool = pool

        result = await alloc_module.allocate_resources("SCAN-TEST-QUEUE", "High")
        assert result.icu_bed_assigned is False
        assert result.queue_position is not None
        assert result.queue_position >= 1
