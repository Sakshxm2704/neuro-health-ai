import pytest
import random
from fastapi.testclient import TestClient
from faker import Faker

from main import app   # your FastAPI app

client = TestClient(app)
fake = Faker()


# -----------------------------
# 1. VALID TEST CASES (300)
# -----------------------------
def generate_valid_cases(n=300):
    cases = []
    for i in range(n):
        cases.append({
            "patient_id": f"PT-{i}",
            "name": fake.name(),
            "age": random.randint(1, 100),
            "symptoms": ["headache", "fatigue"]
        })
    return cases


# -----------------------------
# 2. EDGE CASES (300)
# -----------------------------
def generate_edge_cases(n=300):
    cases = []

    edge_ages = [0, 1, 120, -1, None, ""]
    names = ["", "A", "@" * 1000, None]
    symptoms = [[], None, [""]]

    for i in range(n):
        cases.append({
            "patient_id": f"EDGE-{i}",
            "name": random.choice(names),
            "age": random.choice(edge_ages),
            "symptoms": random.choice(symptoms)
        })
    return cases


# -----------------------------
# 3. FUZZ TEST CASES (400)
# -----------------------------
def generate_fuzz_cases(n=400):
    cases = []
    for i in range(n):
        cases.append({
            "patient_id": fake.uuid4(),
            "name": fake.text(max_nb_chars=20),
            "age": random.randint(-100, 200),
            "symptoms": [fake.word() for _ in range(random.randint(0, 5))]
        })
    return cases


# -----------------------------
# COMBINE ALL (1000+ CASES)
# -----------------------------
ALL_TEST_CASES = (
    generate_valid_cases(300)
    + generate_edge_cases(300)
    + generate_fuzz_cases(400)
)


# -----------------------------
# ACTUAL TEST
# -----------------------------
@pytest.mark.parametrize("payload", ALL_TEST_CASES)
def test_patient_api(payload):
    response = client.post("/patient", json=payload)

    # Accept both success or controlled failure
    assert response.status_code in [200, 201, 400, 422]