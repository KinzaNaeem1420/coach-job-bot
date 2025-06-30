import json
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_jsonl(file_path, resume=None, job_description=None, force_category=None):
    from .vector_store import vector_store  # Assumed vector store instance
    from .rag_pipeline import retrieve_relevant_questions  # Import RAG retrieval
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return []
    
    # If resume and job_description are provided, use vector store with retrieve_relevant_questions
    if resume and job_description:
        return retrieve_relevant_questions(
            vector_store=vector_store,
            resume=resume,
            job_description=job_description,
            top_k=200,
            skills=None,
            experience_level="mid",
            domains=None,
            force_category=force_category
        )
    
    # Fallback: Read all questions from JSONL file if no resume or job_description
    questions = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        questions.append(type('Document', (), {'page_content': line.strip()}))  # Mimic Document object
                    except Exception as e:
                        logger.warning(f"Failed to parse line in {file_path}: {line.strip()}, Error: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {str(e)}")
        return []
    
    return questions