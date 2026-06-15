from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class EmailSummarizerResult(BaseModel):
    summary: str
    action_items: List[str]
    deadlines: str
    reply_urgency: Literal["urgent", "normal", "no-reply-needed"]
    reply_tone: Optional[str] = None
