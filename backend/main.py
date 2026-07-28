import os
import time
import uuid
from contextlib import asynccontextmanager

from api.process_notes import router as notes_router
from api.qa import router as qa_router
from api.summarize_email import router as email_router
from core.errors import ClarityDeskError
from core.logging import request_id_ctx, setup_structured_logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv()

logger = setup_structured_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup configuration validation and graceful shutdown lifecycle handler.
    Fails fast if invalid provider configuration is detected.
    """
    provider_name = os.getenv("LLM_PROVIDER", "mock").lower()
    valid_providers = {"mock", "gemini", "anthropic"}
    if provider_name not in valid_providers:
        raise RuntimeError(f"Fatal configuration error: Invalid LLM_PROVIDER '{provider_name}'. Must be one of: {valid_providers}")
        
    if provider_name == "gemini" and not os.getenv("GEMINI_API_KEY"):
        logger.warning("Startup warning: LLM_PROVIDER='gemini' but GEMINI_API_KEY is missing from environment.")
    elif provider_name == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        logger.warning("Startup warning: LLM_PROVIDER='anthropic' but ANTHROPIC_API_KEY is missing from environment.")
        
    logger.info(f"ClarityDesk API initialized successfully [Provider: {provider_name.upper()}]")
    yield
    logger.info("ClarityDesk API initiating graceful shutdown...")

app = FastAPI(
    title="ClarityDesk API",
    description="Nonprofit Operations Copilot — AI-powered meeting notes, email summarization, and grounded Q&A.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def request_correlation_middleware(request: Request, call_next):
    """
    Assigns X-Request-ID for operational traceability and emits structured JSON logs.
    """
    req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    token = request_id_ctx.set(req_id)
    start_time = time.time()
    
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        latency_ms = round((time.time() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = req_id
        logger.info(f"Completed request: {request.method} {request.url.path} | Status: {response.status_code} | Latency: {latency_ms}ms")
        return response
    finally:
        request_id_ctx.reset(token)

@app.exception_handler(ClarityDeskError)
async def claritydesk_error_handler(request: Request, exc: ClarityDeskError):
    """Centralized domain error handler returning predictable error taxonomies."""
    logger.error(f"Domain error occurred: [{exc.error_code}] {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "request_id": request_id_ctx.get()
            }
        }
    )

app.include_router(notes_router, prefix="/api", tags=["Notes Processing"])
app.include_router(email_router, prefix="/api", tags=["Email Summarization"])
app.include_router(qa_router, prefix="/api", tags=["Grounded Q&A (RAG)"])

# Kubernetes / Operational Probes
@app.get("/health", tags=["Operational"])
@app.get("/live", tags=["Operational"])
def liveness_probe():
    """Liveness probe for container orchestration."""
    return {"status": "ok", "version": app.version}

@app.get("/ready", tags=["Operational"])
def readiness_probe():
    """Readiness probe verifying active provider configuration."""
    provider = os.getenv("LLM_PROVIDER", "mock")
    return {
        "status": "ready",
        "provider": provider,
        "version": app.version
    }
