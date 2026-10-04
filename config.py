import os
from dotenv import load_dotenv

load_dotenv()

# Ollama Cloud
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_CLOUD_BASE = "https://ollama.com"
OLLAMA_CLOUD_MODEL = os.getenv("OLLAMA_CLOUD_MODEL", "devstral-small-2:24b-cloud")

# Local Ollama
OLLAMA_LOCAL_BASE = "http://localhost:11434"
OLLAMA_LOCAL_MODEL = os.getenv("OLLAMA_LOCAL_MODEL", "qwen2.5:1.5b")

# Embedding (always local)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-m3:567m")

# ChromaDB
CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
CHROMA_COLLECTION = "datamedx_patients"

# Data
EXCEL_PATH = os.path.join(os.path.dirname(__file__), "datamedx_veriset_26.xlsx")

# RAG settings
TOP_K_RESULTS = 6
CHUNK_MAX_CHARS = 1500

def use_cloud():
    return bool(OLLAMA_API_KEY)

def get_ollama_base():
    return OLLAMA_CLOUD_BASE if use_cloud() else OLLAMA_LOCAL_BASE

def get_model():
    return OLLAMA_CLOUD_MODEL if use_cloud() else OLLAMA_LOCAL_MODEL

def get_headers():
    if use_cloud():
        return {"Authorization": f"Bearer {OLLAMA_API_KEY}"}
    return {}
