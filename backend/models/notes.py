from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class ActionItem(BaseModel):
    task: str
    owner: str = Field(description="Person responsible. Use 'Unassigned' if not mentioned.")
    deadline: Optional[str] = Field(description="Deadline if mentioned, otherwise null")

class NotesProcessingResult(BaseModel):
    meeting_title: str
    meeting_date: Optional[str]
    summary: str
    decisions: List[str]
    action_items: List[ActionItem]
    confidence: Literal["high", "medium", "low"]
    confidence_note: Optional[str] = None
