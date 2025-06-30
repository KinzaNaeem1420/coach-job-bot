from pydantic import BaseModel
from typing import List

class InterviewRequest(BaseModel):
    resume_name: str
    job_title: str

class InterviewResponse(BaseModel):
    question: str
    category: str
    tags: List[str]

class UserAnswer(BaseModel):
    question: str
    category: str
    tags: List[str]
    user_answer: str

class FeedbackResponse(BaseModel):
    feedback: str

