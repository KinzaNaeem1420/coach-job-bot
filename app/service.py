from .rag_pipeline import retrieve_relevant_questions
from .schemas import InterviewResponse
from fastapi import UploadFile, HTTPException
from fastapi import Form
import json
import os
import random
import datetime
from langchain_community.document_loaders import PyPDFLoader
import google.generativeai as genai
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API key from environment
from dotenv import load_dotenv
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

async def conduct_interview(file: UploadFile, jd: str = Form(max_length=10000)):
    # Validate file type
    if not (file.filename.endswith(".jsonl") or file.filename.endswith(".pdf")):
        raise HTTPException(status_code=400, detail="File must be in JSONL or PDF format")
    
    # Read and validate resume content
    resume_data = []
    if file.filename.endswith(".jsonl"):
        content = await file.read()
        content_str = content.decode("utf-8")
        validate_jsonl_content(content_str)
        resume_lines = content_str.strip().split("\n")
        try:
            resume_data = [json.loads(line) for line in resume_lines if line.strip()]
            if not resume_data:
                raise ValueError("Invalid resume format: no valid data")
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(status_code=400, detail=f"Invalid resume file: {str(e)}")
    else:  # PDF file
        try:
            temp_file = f"temp_{file.filename}"
            with open(temp_file, "wb") as f:
                f.write(await file.read())
            loader = PyPDFLoader(temp_file)
            pdf_docs = loader.load()
            resume_data = [{"content": doc.page_content, "metadata": doc.metadata} for doc in pdf_docs]
            if not resume_data or not any(d["content"].strip() for d in resume_data):
                raise ValueError("PDF resume is empty or contains no valid text")
            os.remove(temp_file)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")
    
    # Prepare job description data
    job_data = {"description": jd, "skills_required": [], "title": "Temporary JD"}
    job_content = json.dumps(job_data)
    
    # Extract resume content
    resume_content = json.dumps(resume_data[0]) if file.filename.endswith(".jsonl") else resume_data[0]["content"]
    if not resume_content.strip():
        raise HTTPException(status_code=400, detail="Resume content is empty")
    
    # Define interview phases
    phases = ["introductory", "basics", "problem solving"]
    
    # Track selected questions to avoid duplicates
    used_questions = set()
    final_questions = []
    
    # Load and process questions for each phase
    model_to_use = "models/gemini-2.5-flash"
    if model_to_use not in [m.name for m in genai.list_models()]:
        raise HTTPException(status_code=500, detail="Gemini-2.5-flash model not available")
    
    # Initialize vector store
    from .vector_store import vector_store  # Assumed vector store instance
    
    for phase in phases:
        # Retrieve questions directly from vector store
        formatted_questions = retrieve_relevant_questions(
            vector_store=vector_store,
            resume=resume_content,
            job_description=job_content,
            top_k=200,
            skills=None,
            experience_level="mid",
            domains=None,
            force_category=phase
        )
        if not formatted_questions:
            logger.error(f"No questions found for {phase} phase")
            raise HTTPException(status_code=500, detail=f"No interview questions available for {phase} phase")
        
        # Validate questions
        valid_questions = [
            q for q in formatted_questions
            if isinstance(q, dict) and "question" in q and "category" in q and q["category"].lower() == phase
        ]
        if not valid_questions:
            logger.error(f"No valid questions parsed for {phase} phase")
            raise HTTPException(status_code=500, detail=f"No valid interview questions available for {phase} phase")
        
        # Select up to 20 questions to avoid token limit
        filtered_questions = random.sample(valid_questions, min(len(valid_questions), 20)) if valid_questions else []
        if not filtered_questions:
            logger.error(f"No questions available for {phase} phase after filtering")
            raise HTTPException(status_code=500, detail=f"No questions available for {phase} phase")
        
        logger.info(f"Retrieved {len(filtered_questions)} questions for {phase} phase")
        
        # Use Gemini to select and enhance 3 questions
        prompt = f"""Current timestamp: {datetime.datetime.now().isoformat()}
Based on the following resume and job description, select 3 interview questions *verbatim* from the provided question list for the '{phase}' phase. Optionally, rephrase the questions to better align with the specific skills and experiences in the resume and job description, but only if the rephrased question remains true to the original intent and category. Ensure the questions are highly tailored to the candidate's background and job requirements. For the '{phase}' phase, only select questions with the '{phase}' category. Ensure the selected questions are not already used in other phases.

The phases are defined as:
- 'introductory': Questions about the candidate's background, experience, and general fit (e.g., "How have you used Airflow in past projects?" rather than technical details like "How do you optimize PostgreSQL queries?").
- 'basics': Questions testing fundamental technical knowledge and skills (e.g., explaining tools or concepts like SQL or FastAPI).
- 'problem solving': Questions requiring the candidate to solve hypothetical problems or design solutions (e.g., system design or optimization).

Question List (all questions have category '{phase}'):
{json.dumps(filtered_questions, indent=1)}

Select exactly 3 unique questions for the '{phase}' phase. Return a JSON array of 3 objects, each with 'original_question' (the verbatim question from the list) and 'enhanced_question' (the rephrased question or the original if no rephrasing is needed), e.g., [{{"original_question": "question 1", "enhanced_question": "rephrased question 1"}}, ...]. Return no additional text, explanations, or markdown.

Resume: {resume_content}
Job Description: {jd}"""
        
        try:
            response = genai.GenerativeModel(model_to_use).generate_content(prompt)
            logger.info(f"Gemini response for {phase} questions: {response.text}")
            if not response.text or response.text.strip() == "":
                logger.error(f"Gemini returned empty response for {phase} questions")
                selected_questions = [
                    {"original_question": q["question"], "enhanced_question": q["question"]}
                    for q in random.sample(filtered_questions, min(len(filtered_questions), 3))
                    if q["question"] not in used_questions
                ]
                if len(selected_questions) < 3:
                    available_questions = [q for q in filtered_questions if q["question"] not in used_questions]
                    selected_questions.extend([
                        {"original_question": q["question"], "enhanced_question": q["question"]}
                        for q in random.sample(available_questions, min(len(available_questions), 3 - len(selected_questions)))
                    ])
            else:
                try:
                    response_text = response.text.strip()
                    start_idx = response_text.find('[')
                    end_idx = response_text.rfind(']') + 1
                    if start_idx == -1 or end_idx == 0:
                        logger.warning(f"No valid JSON array found in Gemini response for {phase}: {response_text}")
                        raise json.JSONDecodeError("No JSON array found", response_text, 0)
                    json_str = response_text[start_idx:end_idx]
                    selected_questions = json.loads(json_str)
                    if not isinstance(selected_questions, list) or len(selected_questions) != 3 or not all(
                        isinstance(q, dict) and "original_question" in q and "enhanced_question" in q for q in selected_questions
                    ):
                        logger.warning(f"Invalid Gemini response format for {phase}: {response_text}")
                        raise json.JSONDecodeError("Invalid JSON format", response_text, 0)
                    
                    valid_questions = []
                    for q in selected_questions:
                        if (
                            q["original_question"] in [fq["question"] for fq in filtered_questions] and
                            any(fq["category"].lower() == phase for fq in filtered_questions if fq["question"] == q["original_question"]) and
                            q["original_question"] not in used_questions
                        ):
                            valid_questions.append(q)
                    
                    if len(valid_questions) < 3:
                        logger.warning(f"Gemini selected invalid or non-{phase} questions for {phase}: {selected_questions}")
                        valid_questions = [
                            {"original_question": q["question"], "enhanced_question": q["question"]}
                            for q in random.sample(filtered_questions, min(len(filtered_questions), 3))
                            if q["question"] not in used_questions
                        ]
                        if len(valid_questions) < 3:
                            available_questions = [q for q in filtered_questions if q["question"] not in used_questions]
                            valid_questions.extend([
                                {"original_question": q["question"], "enhanced_question": q["question"]}
                                for q in random.sample(available_questions, min(len(available_questions), 3 - len(valid_questions)))
                            ])
                    selected_questions = valid_questions
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse Gemini response for {phase}: {response.text}, Error: {str(e)}")
                    selected_questions = [
                        {"original_question": q["question"], "enhanced_question": q["question"]}
                        for q in random.sample(filtered_questions, min(len(filtered_questions), 3))
                        if q["question"] not in used_questions
                    ]
                    if len(selected_questions) < 3:
                        available_questions = [q for q in filtered_questions if q["question"] not in used_questions]
                        selected_questions.extend([
                            {"original_question": q["question"], "enhanced_question": q["question"]}
                            for q in random.sample(available_questions, min(len(available_questions), 3 - len(selected_questions)))
                        ])
        
        except Exception as e:
            logger.error(f"Gemini API call failed for {phase} questions: {str(e)}")
            selected_questions = [
                {"original_question": q["question"], "enhanced_question": q["question"]}
                for q in random.sample(filtered_questions, min(len(filtered_questions), 3))
                if q["question"] not in used_questions
            ]
            if len(selected_questions) < 3:
                available_questions = [q for q in filtered_questions if q["question"] not in used_questions]
                selected_questions.extend([
                    {"original_question": q["question"], "enhanced_question": q["question"]}
                    for q in random.sample(available_questions, min(len(available_questions), 3 - len(selected_questions)))
                ])
        
        # Add questions to final response
        for q in selected_questions[:3]:
            question_data = next((fq for fq in filtered_questions if fq["question"] == q["original_question"]), {"category": phase, "tags": ["general"]})
            final_questions.append(InterviewResponse(
                question=q["enhanced_question"],
                category=question_data["category"],
                tags=question_data["tags"] ,
                phase=phase.capitalize(),
                user_answer=""
            ))
            used_questions.add(q["original_question"])
    
    logger.info(f"Final questions generated: {len(final_questions)}")
    return final_questions

def validate_jsonl_content(content_str):
    """Validate JSONL content."""
    lines = content_str.strip().split("\n")
    for line in lines:
        if line.strip():
            try:
                json.loads(line)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSONL format")