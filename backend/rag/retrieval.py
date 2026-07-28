from typing import Any

import numpy as np
from rag.embeddings import generate_embedding
from rag.reranker import cross_encoder_rerank
from sklearn.metrics.pairwise import cosine_similarity

# In-memory store: list of dicts: {"text": str, "embedding": list[float], "metadata": dict}
vector_store = []

def store_chunks(chunks: list[dict[str, Any]]):
    """
    Chunks should already have 'text', 'metadata', and 'embedding' keys.
    """
    vector_store.extend(chunks)

def get_top_k_cosine(question: str, k: int = 10) -> list[dict[str, Any]]:
    if not vector_store:
        return []
        
    q_embedding = generate_embedding(question)
    
    # Extract all document embeddings
    doc_embeddings = np.array([item["embedding"] for item in vector_store])
    q_embedding_np = np.array([q_embedding])
    
    # Calculate cosine similarity
    similarities = cosine_similarity(q_embedding_np, doc_embeddings)[0]
    
    # Get top k indices
    top_k_indices = np.argsort(similarities)[::-1][:k]
    
    results = []
    for idx in top_k_indices:
        results.append({
            "text": vector_store[idx]["text"],
            "metadata": vector_store[idx]["metadata"],
            "score": float(similarities[idx])
        })
        
    return results

def retrieve_context(question: str) -> list[dict[str, Any]]:
    # 1. Cosine Similarity Search (Top 10)
    candidates = get_top_k_cosine(question, k=10)
    
    if not candidates:
        return []
        
    # 2. Cross Encoder Re-Ranking (Top 3)
    reranked = cross_encoder_rerank(question, candidates)
    
    return reranked[:3]

def clear_store():
    vector_store.clear()
