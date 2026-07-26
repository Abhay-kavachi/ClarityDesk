# ADR-002: Model-Agnostic LLM Provider Abstraction Layer

## Status
Accepted

## Context
ClarityDesk relies on structured LLM outputs (via Pydantic schema validation) for Notes Processing, Email Summarization, and Grounded Q&A.
Originally, the service layer was tightly coupled to the Anthropic Python SDK (`AnthropicService`). During development, testing costs and API key availability created friction.

## Decision
We implemented a model-agnostic provider abstraction layer (`LLMProvider`) with three concrete implementations:
- `AnthropicProvider` (Claude 3.5 Sonnet)
- `GeminiProvider` (Gemini 2.0 Flash via official `google-genai` SDK)
- `MockProvider` (Offline deterministic schema-conforming responses)

The active provider is dynamically instantiated at runtime via the `LLM_PROVIDER` environment variable (`get_llm_provider()`).

## Rationale & Tradeoffs
1. **Zero Vendor Lock-In:** Business logic in route handlers (`/api/process-notes`, `/api/summarize-email`, `/api/ask`) is completely decoupled from SDK-specific payload formatting or error structures.
2. **Offline Testability:** The `MockProvider` enables continuous integration (CI) and local end-to-end evaluation (`evaluation/eval.py`) to execute in ~0.01 seconds with zero API cost or network dependence.
3. **Rollback Safety:** The legacy `anthropic_service.py` module was refactored into a 14-line compatibility wrapper around `AnthropicProvider`, ensuring zero duplicate code while preserving backwards compatibility.
