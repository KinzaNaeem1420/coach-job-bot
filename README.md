## Job-Interview-Coach-Bot
A robust backend API for conducting mock interviews, generating tailored questions, and providing feedback, built with FastAPI and a Retrieval-Augmented Generation (RAG) pipeline.
## Project Structure
```
Job-Interview-Coach-Bot/
├── app/
│   ├── __init__.py
│   ├── embedding.py          # Vector store creation with FAISS and HuggingFaceEmbeddings
│   ├── main.py              # FastAPI application entry point
│   ├── rag_pipeline.py      # RAG retrieval logic
│   ├── repository.py        # Data access layer for JSONL files
│   ├── routes.py            # API endpoints definition
│   ├── schemas.py           # Pydantic models for validation
│   └── service.py           # Business logic layer (RAG and Gemini enhancement)
├── data/                    # Directory for resume, JD, and interview question data (e.g., interview-questions.jsonl)
├── .env                     # Environment variables
├── .gitignore               # Git ignore file
├── requirements.txt         # Python dependencies
└── README.md                # This file
```


## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/your-username/Job-Interview-Coach-Bot.git
cd Job-Interview-Coach-Bot

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Linux/Mac: source venv/bin/activate
# On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
```
Update the `.env` file with your API keys:
# Google Generative AI Configuration
GOOGLE_API_KEY=your-google-api-key-hereiedb
```

### 3.  Run the Application
```
# Start the application to create the vector store and serve the API
uvicorn app.main:app --reload
```

### Example Session
```
# Start the server
$ uvicorn app.main:app --reload
INFO: Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)

# Conduct an interview
$ curl -X POST http://127.0.0.1:8000/conduct_interview/ -F "file=@data/sample-resumes.jsonl" -F "jd=Data Engineer" -H "Content-Type: multipart/form-data"
[
  {"question": "1. Can you elaborate on your Python experience?", "category": "Introductory", "tags": ["general"], "phase": "Introductory"},
  {"question": "2. What motivated your data engineering career?", "category": "Introductory", "tags": ["general"], "phase": "Introductory"},
  {"question": "3. How do you approach new projects?", "category": "Introductory", "tags": ["general"], "phase": "Introductory"},
  ...
]

# Note: Replace <file> with your resume JSONL file path
```
### Configuration Options
```
Database Providers
| Provider  | Notes |
|-----------|-------|
| None      | Uses in-memory vector store (FAISS) for RAG |

Environment Variables
| Variable      | Description |
|---------------|-------------|
| `GOOGLE_API_KEY` | API key for Google Generative AI (Gemini) |

Features
| Feature            | Description |
|--------------------|-------------|
| `RAG Pipeline`     | Retrieves and enhances questions using vector store and Gemini |
| `Question Generation` | Generates 3 questions per phase (Introductory, Basics, Problem Solving) |
| `File Upload`      | Accepts resume files via API |
```




   
