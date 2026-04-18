"""
Model Loader — Singleton
========================
Loads the trained .h5 model once at startup.
Provides a predict() interface used by the prediction service.
"""

import os
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy-loaded model instance
_model = None


def load_model(model_path: str):
    """Load TensorFlow model from disk (called once at startup)."""
    global _model
    if _model is not None:
        return _model

    import tensorflow as tf

    if not os.path.exists(model_path):
        logger.warning(
            "⚠️  Model not found at '%s'. Run ai/model/train_model.py first. "
            "Using random weights for demo.", model_path
        )
        # Return a freshly built (untrained) model for demo purposes
        from ai.model.train_model import build_cnn
        from config import get_settings
        _model = build_cnn(get_settings().image_size)
    else:
        _model = tf.keras.models.load_model(model_path)
        logger.info("✅ Model loaded from '%s'", model_path)

    return _model


def predict_image(image_array: np.ndarray, model_path: str) -> dict:
    """
    Run inference on a preprocessed image array.

    Parameters
    ----------
    image_array : np.ndarray  shape (1, H, W, 1)  float32 in [0, 1]
    model_path  : str

    Returns
    -------
    dict with:
        tumor_detected  : bool
        confidence      : float  (0–1, probability of tumor)
        raw_score       : float
    """
    model = load_model(model_path)

    raw_score = float(model.predict(image_array, verbose=0)[0][0])
    tumor_detected = raw_score >= 0.5
    confidence = raw_score if tumor_detected else (1.0 - raw_score)

    return {
        "tumor_detected": tumor_detected,
        "confidence": round(confidence, 4),
        "raw_score": round(raw_score, 4),
    }
