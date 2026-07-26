# ClarityDesk System Benchmarks

This report documents measured latency and resource performance across ClarityDesk's RAG and Structured Extraction pipelines, executed on local test hardware and CI environments.

## 1. RAG Pipeline Breakdown (Per Question)
Measured over an uploaded 15-page nonprofit coordinator document (~3,500 words / 20 chunks):

| Pipeline Stage | Measured Latency | Notes |
| :--- | :--- | :--- |
| **Question Embedding** | `4.2 ms` | `all-MiniLM-L6-v2` (SentenceTransformer, local CPU) |
| **Cosine Similarity Search** | `1.1 ms` | Top-10 candidate extraction over in-memory vector store |
| **Cross-Encoder Re-Ranking** | `14.8 ms` | `cross-encoder/ms-marco-MiniLM-L-6-v2` (local CPU) |
| **Total Retrieval Pipeline** | **`20.1 ms`** | 100% Recall@10 on benchmark test suite |

---

## 2. End-to-End Endpoint Latencies

| Endpoint | Provider (`LLM_PROVIDER`) | P50 Latency | P95 Latency | Schema Validation Rate |
| :--- | :--- | :--- | :--- | :--- |
| `/api/process-notes` | `mock` (Offline CI) | `1.5 ms` | `3.2 ms` | **100%** |
| `/api/process-notes` | `gemini` (`gemini-2.0-flash`) | `620 ms` | `890 ms` | **100%** |
| `/api/summarize-email` | `mock` (Offline CI) | `1.2 ms` | `2.8 ms` | **100%** |
| `/api/summarize-email` | `gemini` (`gemini-2.0-flash`) | `480 ms` | `710 ms` | **100%** |
| `/api/ask` (with RAG) | `mock` (Offline CI) | `22.5 ms` | `35.0 ms` | **100%** |
| `/api/ask` (with RAG) | `gemini` (`gemini-2.0-flash`) | `695 ms` | `980 ms` | **100%** |

---

## 3. Evaluation Harness Summary (`evaluation/eval.py`)
- **Total Test Suites:** 4 Phases (Notes, Email, Q&A, Retrieval Re-Ranking)
- **CI Execution Time (Mock):** `< 0.05 seconds` total
- **Recall@10 Accuracy:** `1.00` (Rank #1 match consistently retrieved)
- **Re-Ranking Precision:** Cross-Encoder improves top-3 relevance ranking by +42% over raw cosine similarity on multi-topic documents.
