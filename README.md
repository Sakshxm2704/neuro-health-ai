# 🧠 Intelligent Healthcare Ecosystem — Neurology Focus

A production-ready FastAPI backend for AI-powered brain tumor detection, risk classification, clinical decision support, and hospital resource allocation.

---

## Architecture Overview

```
POST /upload-mri
       │
       ▼
┌─────────────────────┐
│  Image Preprocessing │  ← Pillow: grayscale, resize, normalize
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   CNN Model (TF)    │  ← brain_tumor_cnn.h5 → confidence score
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Risk Classifier    │  ← tumor size + confidence → Low/Medium/High
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Decision Engine    │  ← risk + patient data → urgency + next steps
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Resource Allocator  │  ← ICU bed, Doctor, OT room assignment
└─────────┬───────────┘
          │
          ▼
     MongoDB + API Response
```

---

## Folder Structure

```
neuro_health/
│
├── main.py                          # FastAPI app entry point
├── config.py                        # Environment settings (Pydantic)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
│
├── ai/
│   ├── model/
│   │   ├── train_model.py           # STEP 1: CNN training script
│   │   └── model_loader.py          # Singleton model loader for inference
│   └── preprocessing/
│       └── image_processor.py       # STEP 1b: Image → tensor pipeline
│
├── engine/
│   ├── risk_classifier.py           # STEP 2: Risk matrix logic
│   └── decision_engine.py           # STEP 3: Clinical decision tree
│
├── resources/
│   └── allocator.py                 # STEP 4: ICU/Doctor/OT allocation
│
├── api/
│   └── routes/
│       ├── mri.py                   # POST /upload-mri
│       ├── prediction.py            # GET  /prediction/{scan_id}
│       ├── decision.py              # GET  /decision/{scan_id}
│       └── resources.py             # GET  /resources
│
├── database/
│   ├── connection.py                # MongoDB Motor async client
│   └── repository.py               # CRUD operations (Scan/Decision/Allocation)
│
├── utils/
│   └── logger.py                    # Centralized logging
│
├── tests/
│   └── test_core.py                 # pytest suite (no live DB required)
│
└── sample_responses/
    └── api_responses.json           # STEP 7: Sample JSON for all endpoints
```

---

## Quick Start

### Option A — Local Python

```bash
# 1. Clone & enter directory
cd neuro_health

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and configure environment
cp .env.example .env
# Edit .env: set MONGO_URI if not using localhost

# 5. Train the CNN model (generates synthetic data, ~2 min)
python ai/model/train_model.py

# 6. Start MongoDB (skip if already running)
mongod --dbpath /tmp/mongo &

# 7. Run the API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 8. Open interactive docs
# http://localhost:8000/docs
```

### Option B — Docker Compose (zero-config)

```bash
# Build and start everything (MongoDB + API)
docker-compose up --build

# API available at http://localhost:8000
# Docs at       http://localhost:8000/docs
```

---

## API Endpoints

| Method   | Endpoint                              | Description                              |
|----------|---------------------------------------|------------------------------------------|
| `POST`   | `/api/v1/upload-mri`                  | Upload MRI → full analysis pipeline      |
| `GET`    | `/api/v1/prediction/{scan_id}`        | Retrieve CNN prediction + risk           |
| `GET`    | `/api/v1/decision/{scan_id}`          | Retrieve clinical decision               |
| `GET`    | `/api/v1/resources`                   | Hospital resource dashboard              |
| `GET`    | `/api/v1/resources/allocation/{id}`   | Allocation detail for one scan           |
| `DELETE` | `/api/v1/resources/release/{scan_id}` | Discharge patient, release resources     |
| `GET`    | `/`                                   | Health check                             |

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific class
pytest tests/test_core.py::TestRiskClassifier -v
pytest tests/test_core.py::TestDecisionEngine -v
pytest tests/test_core.py::TestPreprocessing  -v
pytest tests/test_core.py::TestResourceAllocator -v
```

---

## Risk Classification Matrix

| Tumor Size | Confidence | Risk Level |
|------------|------------|------------|
| No tumor   | any        | **Low**    |
| Small      | any        | **Low**    |
| Medium     | < 0.75     | **Low**    |
| Medium     | ≥ 0.75     | **Medium** |
| Large      | < 0.80     | **Medium** |
| Large      | ≥ 0.80     | **High**   |

**Escalation modifiers:**
- Patient age ≥ 65 + Medium → escalates to High protocol
- Seizure symptom + Medium → urgency becomes Immediate

---

## Resource Allocation Logic

| Risk Level | ICU Bed | Doctor | OT Room | Priority |
|------------|---------|--------|---------|----------|
| High       | ✅      | ✅     | ✅      | 1st      |
| Medium     | ❌      | ✅     | ❌      | 2nd      |
| Low        | ❌      | ✅ (scheduled) | ❌ | 3rd  |

- If ICU exhausted for High-risk → patient enters **PRIORITY queue** + admin alert
- Thread-safe via `asyncio.Lock`
- Release endpoint (`DELETE /resources/release`) frees resources on discharge

---

## Environment Variables

| Variable        | Default                    | Description              |
|-----------------|----------------------------|--------------------------|
| `MONGO_URI`     | `mongodb://localhost:27017`| MongoDB connection string |
| `MONGO_DB`      | `neuro_health_db`          | Database name            |
| `MODEL_PATH`    | `ai/model/brain_tumor_cnn.h5` | Trained model path    |
| `IMAGE_SIZE`    | `128`                      | CNN input size (px)      |
| `TOTAL_ICU_BEDS`| `10`                       | Hospital ICU capacity    |
| `TOTAL_DOCTORS` | `5`                        | Available doctors        |
| `TOTAL_OT_ROOMS`| `3`                        | Operating theatres       |

---

## Tech Stack

- **FastAPI** — async REST API framework
- **TensorFlow 2.x** — CNN model training and inference
- **Pillow** — image loading and preprocessing
- **Motor** — async MongoDB driver
- **Pydantic v2** — request/response validation
- **pytest + pytest-asyncio** — test suite

---

## Production Considerations

- Replace in-memory resource pool with **Redis** for multi-instance deployments
- Add **JWT authentication** to all endpoints
- Swap synthetic training data with **real labeled MRI dataset** (e.g., Brain Tumor MRI Dataset on Kaggle)
- Add **Prometheus metrics** endpoint for monitoring
- Use **Celery** for async model inference on large files
