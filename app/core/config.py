"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings.

    Values are read from environment variables and, during local development,
    from the project-level ``.env`` file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Hospital RAG Assistant"
    app_env: Literal["development", "testing", "production"] = "development"
    debug: bool = Field(default=True, validation_alias="APP_DEBUG")
    api_v1_prefix: str = "/api/v1"

    database_url: str = "sqlite:///./hospital.db"

    secret_key: str = "change-this-development-secret"
    access_token_expire_minutes: int = 60
    jwt_algorithm: str = "HS256"

    embedding_backend: Literal["sentence_transformers", "hash"] = (
        "sentence_transformers"
    )
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: str | None = None
    embedding_dimension: int = 384

    llm_provider: Literal["retrieval_only", "local_hf", "groq"] = "retrieval_only"
    local_llm_model: str = "google/flan-t5-base"
    local_llm_device: int = -1
    local_llm_max_new_tokens: int = 256

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    chunk_size: int = 220
    chunk_overlap: int = 40
    retrieval_top_k: int = 4
    retrieval_min_score: float = 0.35

    vector_index_path: Path = Path("storage/vector_index/hospital.index")
    vector_metadata_path: Path = Path("storage/vector_index/metadata.json")
    vector_numpy_path: Path = Path("storage/vector_index/hospital_vectors.npz")
    knowledge_base_path: Path = Path("data/knowledge_base")
    knowledge_upload_path: Path = Path("data/knowledge_base/uploads")

    save_chat_history: bool = True
    websocket_max_message_chars: int = 4000
    document_max_upload_mb: int = 15
    document_max_batch_files: int = 50
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""

    return Settings()
