# src/api/models/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class QuestionRequest(BaseModel):
    question: str

class QuestionResponse(BaseModel):
    answer: str
    refs: List[str]
    domain: str
    status: str = "success"

class ScrapeRequest(BaseModel):
    stage: int # 1 to 8
