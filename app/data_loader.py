from langchain_core.documents import Document
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_jsonl(file_path):
    """Load JSONL file as LangChain documents."""
    documents = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                if line.strip():
                    try:
                        data = json.loads(line)
                        if file_path.endswith("sample-resumes.jsonl"):
                            content = " ".join(data.get("skills", []) + [data.get("summary", "")])
                        elif file_path.endswith("sample-job-descriptions.jsonl"):
                            content = data.get("description", "")
                        elif file_path.endswith("interview-questions.jsonl"):
                            content = " ".join([data.get("question", ""), data.get("category", "")] + data.get("tags", []))
                        documents.append(Document(page_content=json.dumps(data), metadata={"source": file_path, "line": i}))
                        logger.info(f"Loaded document from {file_path} line {i}: {data}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in {file_path} at line {i}: {e}")
                        continue
        logger.info(f"Loaded {len(documents)} documents from {file_path}")
        return documents
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Failed to load {file_path}: {e}")
        return []