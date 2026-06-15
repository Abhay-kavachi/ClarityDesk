from pydantic import BaseModel
from typing import Optional

class QAResult(BaseModel):
    answer: str
    source_citation: Optional[str] = None
    matched_text: Optional[str] = None
    found: bool
