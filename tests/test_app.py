from fastapi.testclient import TestClient
from app import app


def test_get_index():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "GraphPatch-AI" in response.text
    assert "Trigger Repair" in response.text


def test_get_cases():
    client = TestClient(app)
    response = client.get("/api/cases")
    assert response.status_code == 200
    data = response.json()
    assert "cases" in data
    assert len(data["cases"]) == 10
    case_ids = [c["id"] for c in data["cases"]]
    assert "case_01_off_by_one" in case_ids
    assert "case_10_external_import" in case_ids


def test_post_run_agent():
    client = TestClient(app)
    payload = {"case_name": "case_01_off_by_one"}
    response = client.post("/api/run-agent", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "failed -> passed" in data["test_status"]
    assert "def get_last_n_items" in data["isolated_code"]
    assert data["model_used"] == "Nemotron-Lightning & Nemotron-Ultra"
    assert "--- a/solution.py" in data["unified_patch"]
    assert "tokens_used" in data
    assert data["tokens_used"]["total"] > 0
    assert data["latency_s"] >= 0
