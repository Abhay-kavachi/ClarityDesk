import os
import pytest
from fastapi.testclient import TestClient

# Ensure mock provider is used for tests
os.environ["LLM_PROVIDER"] = "mock"

from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data

def test_liveness_and_readiness_probes():
    live_resp = client.get("/live")
    assert live_resp.status_code == 200
    assert live_resp.json()["status"] == "ok"

    ready_resp = client.get("/ready")
    assert ready_resp.status_code == 200
    assert ready_resp.json()["status"] == "ready"

def test_openapi_and_swagger():
    openapi_resp = client.get("/openapi.json")
    assert response_is_ok(openapi_resp)
    schema = openapi_resp.json()
    assert "paths" in schema
    assert "/api/process-notes" in schema["paths"]
    assert "/api/summarize-email" in schema["paths"]
    assert "/api/ask" in schema["paths"]

def response_is_ok(resp):
    return resp.status_code == 200

def test_correlation_id_propagation():
    headers = {"X-Request-ID": "test123-correlation-id"}
    response = client.get("/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == "test123-correlation-id"

def test_process_notes_endpoint():
    response = client.post(
        "/api/process-notes",
        json={"notes": "Q3 Budget Review: Approve $10k for marketing. Assign to Sarah by Friday."}
    )
    assert response.status_code == 200
    data = response.json()
    assert "decisions" in data
    assert "action_items" in data

def test_summarize_email_endpoint():
    response = client.post(
        "/api/summarize-email",
        json={"email_content": "Please review the attached grant proposal before Monday."}
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "action_items" in data

def test_qa_endpoint_without_docs():
    response = client.post(
        "/api/ask",
        json={"question": "What is the budget?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["found"] is False
