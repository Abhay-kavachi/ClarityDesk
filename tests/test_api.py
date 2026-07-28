import os

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

def test_qa_endpoint_with_docs_and_clear_documents():
    # 1. Upload a document
    doc_bytes = b"Jose will reach out to the Hartley Foundation by this Friday to confirm the April 1 grant submission deadline."
    upload_resp = client.post(
        "/api/documents",
        files={"file": ("hartley_grant.txt", doc_bytes, "text/plain")}
    )
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    assert "chunks" in upload_data
    assert upload_data["chunks"] >= 1

    # 2. Ask a question that matches the document
    ask_resp = client.post(
        "/api/ask",
        json={"question": "When is the grant deadline?"}
    )
    assert ask_resp.status_code == 200
    ask_data = ask_resp.json()
    assert ask_data["found"] is True
    assert "April 1" in ask_data["answer"]

    # 3. Clear documents
    clear_resp = client.post("/api/clear-documents")
    assert clear_resp.status_code == 200
    assert clear_resp.json()["message"] == "Store cleared"

def test_domain_error_classes():
    from core.errors import (
        ClarityDeskError,
        DocumentProcessingError,
        EmbeddingError,
        ProviderTimeoutError,
        ProviderUnavailableError,
        RetrievalError,
    )
    assert isinstance(RetrievalError("test"), ClarityDeskError)
    assert isinstance(EmbeddingError("test"), ClarityDeskError)
    assert isinstance(ProviderTimeoutError("anthropic", "test"), ClarityDeskError)
    assert isinstance(ProviderUnavailableError("gemini", "test"), ClarityDeskError)
    assert isinstance(DocumentProcessingError("file.pdf", "test"), ClarityDeskError)
