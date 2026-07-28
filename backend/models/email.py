from typing import Literal

from pydantic import BaseModel


class EmailSummarizerResult(BaseModel):
    summary: str
    action_items: list[str]
    deadlines: str
    reply_urgency: Literal["urgent", "normal", "no-reply-needed"]
    reply_tone: str | None = None
