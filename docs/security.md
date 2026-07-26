# ClarityDesk Security Policy & Threat Model

## 1. System Boundary & Scope
ClarityDesk operates as a web co-pilot for nonprofit program coordinators. It ingests unstructured text (meeting notes, email threads) and document files (PDF/DOCX) and communicates with external LLM providers (Google Gemini / Anthropic) to generate structured operational summaries and grounded answers.

---

## 2. Threat Analysis & Hardening Controls

### A. Prompt Injection & Hallucination Exploits
* **Threat:** Malicious text in uploaded meeting notes or emails attempting to override LLM system instructions or inject untrusted URLs.
* **Control:** 
  - **Strict Pydantic Output Validation:** The application never parses raw LLM markdown into executable UI commands. Every LLM response is deserialized through rigid schema definitions (`NotesProcessingResult`, `EmailSummarizerResult`, `QAResult`).
  - **Strict Citation Contract:** The RAG Q&A pipeline forbids combining retrieved excerpts with external model knowledge. If semantic retrieval does not match a document chunk, the API returns `found: false` with a standardized refusal message.

### B. Denial of Service (DoS) & Resource Exhaustion
* **Threat:** Large file uploads (e.g., multi-gigabyte PDFs) or excessive concurrent requests exhausting local server RAM or third-party API rate limits.
* **Control:**
  - **Chunking Cap:** The document chunker (`rag/chunking.py`) splits texts into 500-word blocks.
  - **Provider Timeout Protection:** External provider calls are wrapped in domain error handling (`ProviderTimeoutError`), preventing hanging ASGI workers.

### C. Secret Exposure & Credential Leakage
* **Threat:** API keys (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`) accidentally committed to source control or logged in tracebacks.
* **Control:**
  - `.env` is explicitly declared in `.gitignore`.
  - Structured JSON logger (`core/logging.py`) excludes environment variables from log payloads.

---

## 3. Operational Observability
* **Correlation IDs:** Every HTTP request is assigned a UUID4 `X-Request-ID` header, propagated through logs to trace failures without exposing sensitive user payload data.
* **Health Probes:** `/health` returns status, active provider, and app version for automated container liveness/readiness probes.
