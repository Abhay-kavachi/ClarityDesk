from typing import Literal

from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    task: str
    owner: str = Field(description="Person responsible. Use 'Unassigned' if not mentioned.")
    deadline: str | None = Field(description="Deadline if mentioned, otherwise null")

class NotesProcessingResult(BaseModel):
    meeting_title: str
    meeting_date: str | None
    summary: str
    decisions: list[str]
    action_items: list[ActionItem]
    confidence: Literal["high", "medium", "low"]
    confidence_note: str | None = None
