import io
import numpy as np
from PIL import Image

def preprocess_image(image_bytes: bytes, target_size: int = 64) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert("L")
    img = img.resize((target_size, target_size), Image.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0
    return arr.reshape(1, target_size, target_size, 1)

def estimate_tumor_size(score: float) -> str:
    if score < 0.60:
        return "small"
    elif score < 0.80:
        return "medium"
    else:
        return "large"
