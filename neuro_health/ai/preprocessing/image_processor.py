"""
STEP 1b — Preprocessing Pipeline
==================================
Converts raw uploaded MRI images into tensors ready for CNN inference.

Steps:
  1. Open image via Pillow
  2. Convert to grayscale
  3. Resize to model input size (default 128×128)
  4. Normalize pixel values to [0, 1]
  5. Reshape to (1, H, W, 1) for batch inference
"""

import io
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


def preprocess_image(image_bytes: bytes, target_size: int = 128) -> np.ndarray:
    """
    Parameters
    ----------
    image_bytes : raw bytes from the uploaded file
    target_size : int — must match the CNN's input size

    Returns
    -------
    np.ndarray of shape (1, target_size, target_size, 1), dtype float32
    """
    try:
        # Open image from bytes
        img = Image.open(io.BytesIO(image_bytes))

        # Convert any color mode to grayscale (MRI is typically grayscale)
        img = img.convert("L")

        # Resize with high-quality Lanczos filter
        img = img.resize((target_size, target_size), Image.LANCZOS)

        # To numpy array and normalize
        arr = np.array(img, dtype=np.float32) / 255.0  # [0, 1]

        # Add batch + channel dims → (1, H, W, 1)
        arr = arr.reshape(1, target_size, target_size, 1)

        logger.debug("Image preprocessed: shape=%s, min=%.3f, max=%.3f",
                     arr.shape, arr.min(), arr.max())
        return arr

    except Exception as e:
        logger.error("Preprocessing failed: %s", e)
        raise ValueError(f"Invalid image data: {e}") from e


def estimate_tumor_size(prediction_map: np.ndarray) -> str:
    """
    Heuristic tumor size estimation from the CNN's raw confidence.
    In a production system this would use segmentation output.

    Returns: 'small' | 'medium' | 'large'
    """
    score = float(prediction_map)
    if score < 0.65:
        return "small"
    elif score < 0.82:
        return "medium"
    else:
        return "large"
