# ClarityDesk

ClarityDesk is an AI-powered operations copilot designed specifically for nonprofit coordinators. Instead of acting as a generic chatbot, ClarityDesk focuses entirely on automating high-friction administrative tasks: extracting action items from messy meeting notes, summarizing long email threads, and instantly querying historical project decisions using a specialized Retrieval-Augmented Generation (RAG) pipeline.

Every decision in this architecture is built to give coordinators back 30 minutes of their day.

## Features

- **Notes Processor:** Instantly extracts decisions, owners, and deadlines from unstructured meeting notes.
- **Email Summarizer:** Condenses long email threads into high-level summaries and precise action items.
- **Strict Q&A (RAG):** Uses local embeddings and cross-encoder re-ranking to cite exact sources for project answers, strictly preventing AI hallucinations.
- **Model-Agnostic Architecture:** Features an `LLMProvider` abstraction layer allowing the backend to hot-swap between Anthropic, Gemini, and Mock testing providers via environment variables.

## Tech Stack

- **Frontend:** React, TypeScript, Vite, TailwindCSS (Lucide Icons)
- **Backend:** Python, FastAPI, Pydantic
- **AI/ML:** `google-genai`, `anthropic`, `sentence-transformers` (all-MiniLM-L6-v2 + ms-marco-MiniLM-L-6-v2)
- **Validation:** Comprehensive custom evaluation harness for accuracy and latency testing.

---

## Local Setup

### 1. Backend

Navigate to the backend directory and set up a virtual environment:
```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file in the `backend` directory:
```env
# Choose your provider: 'mock', 'gemini', or 'anthropic'
LLM_PROVIDER=gemini

# Add your chosen provider's key
GEMINI_API_KEY=your_gemini_key_here
# ANTHROPIC_API_KEY=your_anthropic_key_here
```

Run the API:
```bash
uvicorn main:app --reload
```

### 2. Frontend

Open a new terminal and navigate to the frontend directory:
```bash
cd frontend
npm install
npm run dev
```

### 3. Evaluation Harness

To run the automated tests and verify the RAG pipeline, you can use the built-in evaluation script from the backend directory:
```bash
python ../evaluation/eval.py
```
*(Tip: Set `LLM_PROVIDER=mock` in your `.env` to run the entire test suite instantly and for free without using any API credits).*

### 4. Docker & Container Deployment

To launch the backend API in an isolated container with Kubernetes health probes (`/live` and `/ready`) enabled:
```bash
docker-compose up --build
```
This requires zero local Python or virtualenv configuration and starts the API on port 8000.

---


## Engineering & Operational Documentation

ClarityDesk is built with production-grade engineering discipline, including explicit Architecture Decision Records (ADRs), threat modeling, and structured JSON observability:
- [ADR-001: In-Memory Vector Store vs. External Vector DB](file:///docs/ADR/ADR-001-in-memory-rag-vs-vectordb.md)
- [ADR-002: Model-Agnostic LLM Provider Abstraction Layer](file:///docs/ADR/ADR-002-llm-provider-abstraction.md)
- [Security Policy & Threat Model](file:///docs/security.md)
- [System Latency & Benchmark Table](file:///docs/benchmarks.md)

