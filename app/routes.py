from fastapi import APIRouter, Form, UploadFile, HTTPException
from .service import conduct_interview
from .schemas import InterviewResponse

router = APIRouter()

@router.post("/conduct_interview/")
async def conduct_interview_endpoint(file: UploadFile, jd: str = Form(max_length=10000)):
    return await conduct_interview(file, jd)