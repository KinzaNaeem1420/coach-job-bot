import json
import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Load questions from JSONL file and create vector store
def load_questions_to_vector_store(file_path):
    documents = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        doc = json.loads(line.strip())
                        if "question" in doc and "category" in doc:
                            documents.append(Document(
                                page_content=line.strip(),
                                metadata={"category": doc["category"], "tags": doc.get("tags", [])}
                            ))
                    except json.JSONDecodeError:
                        continue
        if not documents:
            raise ValueError("No valid documents loaded from JSONL")
        return FAISS.from_documents(documents, embeddings)
    except Exception as e:
        raise Exception(f"Failed to load vector store: {str(e)}")

# Initialize vector store
data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
vector_store = load_questions_to_vector_store(os.path.join(data_dir, "interview-questions.jsonl"))