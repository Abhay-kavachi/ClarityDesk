from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
from datetime import datetime
from models.notes import NotesProcessingResult
from prompts.notes import NOTES_PROCESSOR_PROMPT
from services.llm_provider import get_llm_provider

router = APIRouter()
llm_service = get_llm_provider()

class ProcessNotesRequest(BaseModel):
    notes: str

@router.post("/process-notes", response_model=dict)
async def process_notes(request: ProcessNotesRequest):
    try:
        # Prepare the prompt
        prompt = NOTES_PROCESSOR_PROMPT.format(notes_content=request.notes)
        
        # Process with LLM
        validated_result, usage = llm_service.generate_structured(
            prompt=prompt,
            schema=NotesProcessingResult
        )
        
        # Log cost (as requested in the brief)
        log_entry = {
            "endpoint": "/api/process-notes",
            "tokensUsed": usage["tokensUsed"],
            "estimatedCost": round(usage["estimatedCost"], 6),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # In a real app, we might write this to a DB or logger
        with open("cost_log.jsonl", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            
        return validated_result.model_dump()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
