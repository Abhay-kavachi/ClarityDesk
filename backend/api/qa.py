import json
from datetime import UTC, datetime

from fastapi import APIRouter, File, HTTPException, UploadFile
from models.qa import QAResult
from prompts.qa import QA_PROMPT
from pydantic import BaseModel
from rag.chunking import process_document
from rag.embeddings import generate_embeddings_batch
from rag.retrieval import clear_store, retrieve_context, store_chunks
from services.llm_provider import get_llm_provider

router = APIRouter()
llm_service = get_llm_provider()

class AskRequest(BaseModel):
    question: str

@router.post("/documents")
async def upload_document(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        chunks = process_document(file.filename, contents)
        
        if not chunks:
            return {"message": "No text extracted", "chunks": 0}
            
        # Generate embeddings
        texts = [c["text"] for c in chunks]
        embeddings = generate_embeddings_batch(texts)
        
        # Merge embeddings into chunks
        for i, chunk in enumerate(chunks):
            chunk["embedding"] = embeddings[i]
            
        # Store
        store_chunks(chunks)
        
        return {"message": f"Successfully processed {file.filename}", "chunks": len(chunks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/ask", response_model=dict)
async def ask_question(request: AskRequest):
    try:
        # Retrieve chunks with reranking
        top_chunks = retrieve_context(request.question)
        
        if not top_chunks:
            # Nothing uploaded
            return QAResult(
                answer="I couldn't find this in your uploaded notes. The question may be answered in documents that haven't been uploaded yet.",
                found=False
            ).model_dump()
            
        # Format excerpts
        excerpts = []
        for c in top_chunks:
            page_str = f" | page: {c['metadata']['page']}" if c['metadata'].get('page') else " | page: null"
            excerpt = f"[Excerpt]\nfilename: {c['metadata']['filename']} | chunk: {c['metadata']['chunk']}{page_str}\n{c['text']}\n"
            excerpts.append(excerpt)
            
        retrieved_text = "\n".join(excerpts)
        
        # Since the Q&A prompt expects raw text with exact string matches, we will tweak it slightly in the service or just use the base service to ask for JSON.
        # We will wrap the prompt to explicitly request the QAResult JSON.
        prompt = QA_PROMPT.format(user_question=request.question, retrieved_chunks=retrieved_text)
        prompt += "\n\nCRITICAL: You must return the output as a valid JSON object matching the requested schema. If found, include answer, source_citation, and matched_text. If not found, set found=false, and put the 'I couldn't find this...' message in the answer field."
        
        validated_result, usage = llm_service.generate_structured(
            prompt=prompt,
            schema=QAResult
        )
        
        # Log cost
        log_entry = {
            "endpoint": "/api/ask",
            "tokensUsed": usage["tokensUsed"],
            "estimatedCost": round(usage["estimatedCost"], 6),
            "timestamp": datetime.now(UTC).isoformat()
        }
        with open("cost_log.jsonl", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            
        return validated_result.model_dump()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/clear-documents")
async def clear_documents():
    clear_store()
    return {"message": "Store cleared"}
