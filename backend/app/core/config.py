import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

# Base directory for backend
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # API Keys & Models
    GOOGLE_API_KEY: str = ""
    GEMINI_CHAT_MODEL: str = "gemini-3.6-flash"
    GEMINI_EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    
    # Storage & Persistence Paths
    CHROMA_PERSIST_DIRECTORY: str = str(BASE_DIR / "data" / "chroma")
    CHROMA_COLLECTION_NAME: str = "multimodal_rag_collection"
    SQLITE_DB_PATH: str = str(BASE_DIR / "data" / "metadata.db")
    UPLOADS_DIRECTORY: str = str(BASE_DIR / "data" / "uploads")
    PROCESSED_DIRECTORY: str = str(BASE_DIR / "data" / "processed")
    DOCS_DIRECTORY: str = str(BASE_DIR / "docs")

    # Chunking Configuration
    CHUNK_MAX_CHARACTERS: int = 3000
    CHUNK_NEW_AFTER_N_CHARS: int = 2400
    CHUNK_COMBINE_UNDER_N_CHARS: int = 500

    # Feature Flags & Cost Control
    ENABLE_MULTIMODAL_SUMMARY: bool = True
    ENABLE_QUERY_EXPANSION: bool = True
    ENABLE_RERANKING: bool = True

    # Retrieval Defaults
    RETRIEVAL_K: int = 5
    RERANK_TOP_N: int = 10
    FINAL_CONTEXT_K: int = 5
    DEFAULT_RRF_K: int = 60
    DEFAULT_VECTOR_WEIGHT: float = 0.7
    DEFAULT_BM25_WEIGHT: float = 0.3

    # Gemini Resilience
    GEMINI_MAX_RETRIES: int = 3
    GEMINI_RETRY_DELAY_SEC: float = 2.0

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # Security & Protection Settings
    API_KEY: str = ""
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 120
    RATE_LIMIT_BURST: int = 30

@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    # Ensure critical storage directories exist
    os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
    os.makedirs(settings.UPLOADS_DIRECTORY, exist_ok=True)
    os.makedirs(settings.PROCESSED_DIRECTORY, exist_ok=True)
    os.makedirs(settings.DOCS_DIRECTORY, exist_ok=True)
    os.makedirs(os.path.dirname(settings.SQLITE_DB_PATH), exist_ok=True)
    return settings
