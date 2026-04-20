import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "digital-auditor-cisa")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "audit.log")

KNOWLEDGE_RAW_DOCS = PROJECT_ROOT / "knowledge" / "raw_docs"
CHROMA_DB_PATH = PROJECT_ROOT / "chroma_db"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
