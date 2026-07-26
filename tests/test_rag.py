import os
import pytest
from rag.chunking import chunk_text, extract_text_from_txt
from rag.embeddings import generate_embedding
from rag.retrieval import store_chunks, get_top_k_cosine, retrieve_context, clear_store

def test_text_chunking():
    long_text = "word " * 1200
    chunks = chunk_text(long_text, max_words=500)
    assert len(chunks) == 3
    assert len(chunks[0].split()) == 500

def test_embedding_generation():
    emb = generate_embedding("nonprofit coordinator budget review")
    assert isinstance(emb, list)
    assert len(emb) > 0
    assert isinstance(emb[0], float)

def test_rag_store_and_retrieve():
    clear_store()
    sample_chunks = [
        {
            "text": "The annual gala fundraiser is scheduled for October 15th at the civic center.",
            "metadata": {"filename": "gala.txt", "chunk": 1, "page": 1},
            "embedding": generate_embedding("The annual gala fundraiser is scheduled for October 15th at the civic center.")
        },
        {
            "text": "The marketing department needs a 15% budget increase for Q4 campaigns.",
            "metadata": {"filename": "budget.txt", "chunk": 1, "page": 1},
            "embedding": generate_embedding("The marketing department needs a 15% budget increase for Q4 campaigns.")
        }
    ]
    store_chunks(sample_chunks)
    
    results = retrieve_context("When is the gala fundraiser?")
    assert len(results) > 0
    top_match = results[0]
    assert "gala" in top_match["text"].lower()
    assert "rerank_score" in top_match
    clear_store()
