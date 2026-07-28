import json
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from models.email import EmailSummarizerResult
from prompts.email import EMAIL_SUMMARIZER_PROMPT
from pydantic import BaseModel
from services.llm_provider import get_llm_provider

router = APIRouter()
llm_service = get_llm_provider()

class SummarizeEmailRequest(BaseModel):
    email_content: str

@router.post("/summarize-email", response_model=dict)
async def summarize_email(request: SummarizeEmailRequest):
    try:
        # Prepare the prompt
        prompt = EMAIL_SUMMARIZER_PROMPT.format(email_content=request.email_content)
        
        # Process with LLM
        validated_result, usage = llm_service.generate_structured(
            prompt=prompt,
            schema=EmailSummarizerResult
        )
        
        # Log cost
        log_entry = {
            "endpoint": "/api/summarize-email",
            "tokensUsed": usage["tokensUsed"],
            "estimatedCost": round(usage["estimatedCost"], 6),
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        with open("cost_log.jsonl", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            
        return validated_result.model_dump()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
