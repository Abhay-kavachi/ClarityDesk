import io
import pdfplumber
import docx

def extract_text_from_pdf(file_bytes: bytes) -> list[dict]:
    chunks = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                chunks.append({"text": text, "page_number": i + 1})
    return chunks

def extract_text_from_docx(file_bytes: bytes) -> list[dict]:
    # docx doesn't support page numbers easily, we just chunk by paragraph
    doc = docx.Document(io.BytesIO(file_bytes))
    full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    return [{"text": full_text, "page_number": None}]

def extract_text_from_txt(file_bytes: bytes) -> list[dict]:
    text = file_bytes.decode('utf-8', errors='replace')
    return [{"text": text, "page_number": None}]

def chunk_text(text: str, max_words: int = 500) -> list[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i:i + max_words])
        chunks.append(chunk)
    return chunks

def process_document(filename: str, file_bytes: bytes) -> list[dict]:
    """
    Extracts text and chunks it. Returns a list of dicts:
    {"text": "...", "metadata": {"filename": ..., "chunk": ..., "page": ...}}
    """
    ext = filename.lower().split('.')[-1]
    
    if ext == 'pdf':
        page_texts = extract_text_from_pdf(file_bytes)
    elif ext == 'docx':
        page_texts = extract_text_from_docx(file_bytes)
    else:
        page_texts = extract_text_from_txt(file_bytes)
        
    final_chunks = []
    chunk_index = 1
    
    for pt in page_texts:
        sub_chunks = chunk_text(pt["text"], max_words=500)
        for sc in sub_chunks:
            final_chunks.append({
                "text": sc,
                "metadata": {
                    "filename": filename,
                    "chunk": chunk_index,
                    "page": pt["page_number"]
                }
            })
            chunk_index += 1
            
    return final_chunks
