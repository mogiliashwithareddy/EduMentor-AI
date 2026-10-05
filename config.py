from pathlib import Path

APP_NAME = "EduMentor AI"

OLLAMA_MODEL = "llama3.2"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

CHUNK_SIZE = 700
CHUNK_OVERLAP = 120
TOP_K = 4

DATA_DIR = Path("data")
CHROMA_DIR = DATA_DIR / "chroma_db"
CHAT_HISTORY_FILE = DATA_DIR / "chat_history.json"

DATA_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(exist_ok=True)