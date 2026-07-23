"""Validate local database, pgvector, Alembic, embedding and GPU configuration."""

import sys
from pathlib import Path

from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.db.session import SessionLocal

EXPECTED_ALEMBIC_HEAD = "d4b91e697f24"


def ok(label: str, value: object) -> None:
    """Print one successful diagnostic."""

    print(f"[OK] {label}: {value}")


def fail(label: str, value: object) -> None:
    """Print one failed diagnostic."""

    print(f"[FAIL] {label}: {value}")


def check_gpu() -> bool:
    """Verify configured embedding/local-LLM CUDA devices."""

    settings = get_settings()
    needs_cuda = (settings.embedding_device or "").startswith("cuda") or (
        settings.llm_provider == "local_hf"
        and settings.local_llm_device >= 0
    )
    if not needs_cuda:
        ok("GPU", "not requested by current settings")
        return True

    try:
        import torch
    except ImportError:
        fail("GPU", "PyTorch is not installed")
        return False

    if not torch.cuda.is_available():
        fail("GPU", "CUDA requested but torch.cuda.is_available() is false")
        return False
    names = [
        torch.cuda.get_device_name(index)
        for index in range(torch.cuda.device_count())
    ]
    ok("GPU", ", ".join(names))
    return True


def check_database() -> bool:
    """Verify PostgreSQL types, extension, migration and indexed embeddings."""

    try:
        with SessionLocal() as db:
            dialect = db.bind.dialect.name if db.bind is not None else "unknown"
            if dialect != "postgresql":
                fail("Database dialect", f"{dialect}; expected postgresql")
                return False
            ok("Database dialect", dialect)

            extension = db.scalar(
                text(
                    "SELECT extname FROM pg_extension "
                    "WHERE extname = 'vector'"
                )
            )
            if extension != "vector":
                fail("pgvector extension", "not enabled in this database")
                return False
            ok("pgvector extension", extension)

            revision = db.scalar(text("SELECT version_num FROM alembic_version"))
            if revision != EXPECTED_ALEMBIC_HEAD:
                fail(
                    "Alembic revision",
                    f"{revision}; expected {EXPECTED_ALEMBIC_HEAD}",
                )
                return False
            ok("Alembic revision", revision)

            types = db.execute(
                text(
                    """
                    SELECT table_name, column_name, data_type, udt_name
                    FROM information_schema.columns
                    WHERE (table_name, column_name) IN (
                        ('knowledge_chunks', 'embedding'),
                        ('chat_messages', 'sources')
                    )
                    ORDER BY table_name, column_name
                    """
                )
            ).all()
            ok("PostgreSQL special columns", types)

            index_name = db.scalar(
                text(
                    "SELECT indexname FROM pg_indexes "
                    "WHERE indexname = "
                    "'ix_knowledge_chunks_embedding_hnsw'"
                )
            )
            if not index_name:
                fail("HNSW index", "missing")
                return False
            ok("HNSW index", index_name)

            chunks, embedded = db.execute(
                text(
                    "SELECT COUNT(*), COUNT(embedding) "
                    "FROM knowledge_chunks"
                )
            ).one()
            if chunks != embedded:
                fail("Embeddings", f"{embedded}/{chunks} chunks embedded")
                return False
            ok("Embeddings", f"{embedded}/{chunks} chunks embedded")
    except Exception as exc:
        fail("Database connection/schema", exc)
        return False
    return True


def main() -> None:
    """Run all checks and return a shell-friendly status."""

    settings = get_settings()
    ok("Embedding device", settings.embedding_device)
    ok("LLM provider", settings.llm_provider)
    if settings.llm_provider == "local_hf":
        ok("Local LLM model", settings.local_llm_model)

    success = check_gpu() and check_database()
    if not success:
        raise SystemExit(1)
    print("Local setup is ready.")


if __name__ == "__main__":
    main()
