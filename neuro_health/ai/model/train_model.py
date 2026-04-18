"""
STEP 1 — AI Model: Brain Tumor CNN
===================================
• Generates synthetic MRI-like grayscale images (128×128)
• Builds a lightweight CNN for binary classification
  (0 = No Tumor, 1 = Tumor)
• Trains, evaluates, and saves the model as .h5

Run standalone:
    python ai/model/train_model.py
"""

import os
import sys
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
IMG_SIZE    = 128
CHANNELS    = 1          # Grayscale MRI
NUM_SAMPLES = 2000       # Synthetic dataset size
EPOCHS      = 15
BATCH_SIZE  = 32
SAVE_PATH   = os.path.join(os.path.dirname(__file__), "brain_tumor_cnn.h5")


# ── 1. Synthetic Data Generator ────────────────────────────────────────────────
def generate_synthetic_mri(num_samples: int, img_size: int):
    """
    Creates fake MRI-like images using:
      - Gaussian noise base (brain tissue simulation)
      - Bright circular blobs for tumor class
      - Labels: 0 = healthy, 1 = tumor
    """
    X, y = [], []

    for i in range(num_samples):
        label = i % 2  # Alternate healthy/tumor for balanced dataset

        # Base: random Gaussian noise (simulates brain tissue)
        img = np.random.normal(loc=0.3, scale=0.1, size=(img_size, img_size))

        if label == 1:
            # Add a bright elliptical "tumor" blob at random position
            cx = np.random.randint(30, img_size - 30)
            cy = np.random.randint(30, img_size - 30)
            radius_x = np.random.randint(8, 20)
            radius_y = np.random.randint(8, 20)

            for px in range(img_size):
                for py in range(img_size):
                    # Ellipse equation
                    if ((px - cx) ** 2 / radius_x ** 2 +
                            (py - cy) ** 2 / radius_y ** 2) <= 1:
                        img[px, py] += np.random.uniform(0.4, 0.7)

        img = np.clip(img, 0, 1)  # Normalize to [0, 1]
        X.append(img)
        y.append(label)

    X = np.array(X, dtype=np.float32).reshape(-1, img_size, img_size, 1)
    y = np.array(y, dtype=np.int32)
    return X, y


# ── 2. CNN Architecture ────────────────────────────────────────────────────────
def build_cnn(img_size: int) -> keras.Model:
    """
    Lightweight CNN:
      Conv → Pool → Conv → Pool → Dense → Output
    Suitable for grayscale 128×128 MRI classification.
    """
    model = keras.Sequential([
        # Block 1: Edge & texture detection
        layers.Conv2D(32, (3, 3), activation="relu",
                      input_shape=(img_size, img_size, 1), padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D(2, 2),
        layers.Dropout(0.25),

        # Block 2: Higher-level pattern detection
        layers.Conv2D(64, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D(2, 2),
        layers.Dropout(0.25),

        # Block 3: Complex feature extraction
        layers.Conv2D(128, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D(2, 2),
        layers.Dropout(0.4),

        # Classifier head
        layers.Flatten(),
        layers.Dense(256, activation="relu"),
        layers.Dropout(0.5),
        layers.Dense(1, activation="sigmoid"),  # Binary output
    ], name="BrainTumorCNN")

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        loss="binary_crossentropy",
        metrics=["accuracy",
                 keras.metrics.Precision(name="precision"),
                 keras.metrics.Recall(name="recall")],
    )
    return model


# ── 3. Training Pipeline ───────────────────────────────────────────────────────
def train(num_samples=NUM_SAMPLES):
    logger.info("📊 Generating synthetic MRI dataset (%d samples)...", num_samples)
    X, y = generate_synthetic_mri(num_samples, IMG_SIZE)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    logger.info("  Train: %d | Test: %d", len(X_train), len(X_test))

    model = build_cnn(IMG_SIZE)
    model.summary()

    # Callbacks: early stopping + learning rate decay
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=4, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=2, min_lr=1e-6),
    ]

    logger.info("🏋️  Training CNN...")
    history = model.fit(
        X_train, y_train,
        validation_split=0.15,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=callbacks,
        verbose=1,
    )

    # ── 4. Evaluation ─────────────────────────────────────────────────────────
    logger.info("📈 Evaluating model on test set...")
    results = model.evaluate(X_test, y_test, verbose=0)
    metric_names = model.metrics_names
    for name, val in zip(metric_names, results):
        logger.info("  %s: %.4f", name, val)

    y_pred = (model.predict(X_test) > 0.5).astype(int).flatten()
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred,
                                target_names=["No Tumor", "Tumor"]))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    # ── 5. Save Model ──────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    model.save(SAVE_PATH)
    logger.info("✅ Model saved → %s", SAVE_PATH)

    return model, history


if __name__ == "__main__":
    train()
