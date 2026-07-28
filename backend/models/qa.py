
from pydantic import BaseModel


class QAResult(BaseModel):
    answer: str
    source_citation: str | None = None
    matched_text: str | None = None
    found: bool
