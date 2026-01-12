# src/api/models/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class QuestionRequest(BaseModel):
    question: str

class ReferenceDetail(BaseModel):
    title: str
    score: float
    is_primary: bool = False

class QuestionResponse(BaseModel):
    answer: str
    main_reference: Optional[str] = None
    refs: List[ReferenceDetail]
    domain: str
    status: str = "success"

class ScrapeRequest(BaseModel):
    stage: int