# 💼 7. Job Interview Coach Bot
# Use Case: Helps users prep for interviews with personalized Q&A and mock sessions.

# RAG Data:

# Resume, job description, and industry-specific questions.

# Retrieval from job-specific questions banks (Leetcode, Glassdoor, HR blogs).

# FastAPI:

# Upload resumes and job postings.

# Mock interview flow with feedback via /interview, /feedback.
from fastapi import FastAPI
from .routes import router

app = FastAPI()
app.include_router(router)