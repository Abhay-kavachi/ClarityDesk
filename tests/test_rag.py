from rag.chunking import chunk_text
from rag.embeddings import generate_embedding
from rag.retrieval import clear_store, retrieve_context, store_chunks


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

def test_process_document_txt_pdf_docx(monkeypatch):
    from rag.chunking import process_document
    
    # Test txt file processing
    txt_chunks = process_document("notes.txt", b"Grant budget notes for Q3.")
    assert len(txt_chunks) == 1
    assert txt_chunks[0]["metadata"]["filename"] == "notes.txt"
    assert txt_chunks[0]["metadata"]["page"] is None

    # Test pdf file processing via mock
    def mock_pdf_extract(bytes_val):
        return [{"text": "Page 1 content", "page_number": 1}, {"text": "Page 2 content", "page_number": 2}]
    monkeypatch.setattr("rag.chunking.extract_text_from_pdf", mock_pdf_extract)
    pdf_chunks = process_document("report.pdf", b"dummy pdf bytes")
    assert len(pdf_chunks) == 2
    assert pdf_chunks[1]["metadata"]["page"] == 2

    # Test docx file processing via mock
    def mock_docx_extract(bytes_val):
        return [{"text": "Docx full content", "page_number": None}]
    monkeypatch.setattr("rag.chunking.extract_text_from_docx", mock_docx_extract)
    docx_chunks = process_document("memo.docx", b"dummy docx bytes")
    assert len(docx_chunks) == 1
    assert docx_chunks[0]["metadata"]["filename"] == "memo.docx"
