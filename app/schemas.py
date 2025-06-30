from pydantic import BaseModel
from typing import List

class InterviewResponse(BaseModel):
    question: str
    category: str
    tags: List[str]
    phase: str
    

class FeedbackResponse(BaseModel):
    feedback: str