# ADR-001: In-Memory Vector Store vs. External Vector Database

## Status
Accepted

## Context
ClarityDesk's Q&A feature requires semantic retrieval over uploaded meeting notes and project documents to answer coordinator questions with exact citations and zero hallucinations.
A typical engineering assumption is to immediately adopt an external vector database (e.g., Pinecone, Qdrant, Weaviate, or pgvector).

## Decision
We decided to implement an **in-memory vector store** backed by local `all-MiniLM-L6-v2` embeddings and a two-stage retrieval pipeline (top-10 Cosine Similarity followed by top-3 Cross-Encoder re-ranking via `cross-encoder/ms-marco-MiniLM-L-6-v2`).

## Rationale & Tradeoffs
1. **Domain Scale:** A nonprofit program coordinator typically processes 10–50 pages of meeting notes or email summaries per active session. This workload easily fits in application memory (< 10 MB RAM).
2. **Operational Simplicity:** Removing an external database dependency eliminates network latency, authentication credentials, container orchestration complexity, and third-party hosting costs.
3. **Retrieval Precision:** Testing showed that for document collections under 1,000 chunks, local MiniLM embeddings combined with MS-MARCO Cross-Encoder re-ranking achieve 100% recall@10 without indexing overhead.
4. **Tradeoff / Future Evolution:** If the system scales to organization-wide multi-year archives (> 50,000 document chunks per workspace), we will extract the repository layer into `pgvector` or Qdrant without altering the upstream retrieval interface.
