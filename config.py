from pathlib import Path


APP_NAME = "EduMentor AI"

OLLAMA_MODEL = "llama3.2"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

CHUNK_SIZE = 700
CHUNK_OVERLAP = 120
TOP_K = 4


# Project root
BASE_DIR = Path(__file__).resolve().parent


# Data folder
DATA_DIR = BASE_DIR / "data"


# Persistent ChromaDB folder
CHROMA_DIR = DATA_DIR / "chroma_db"


# Persistent chat-history file
CHAT_HISTORY_FILE = DATA_DIR / "chat_history.json"


# Create folders if they do not exist
DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

CHROMA_DIR.mkdir(
    parents=True,
    exist_ok=True
)