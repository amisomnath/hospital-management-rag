"""Shared isolated application fixtures."""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

_TEST_ROOT = Path(tempfile.mkdtemp(prefix="hospital-rag-tests-"))
os.environ["APP_ENV"] = "testing"
os.environ["DEBUG"] = "false"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_ROOT / 'test.db'}"
os.environ["EMBEDDING_BACKEND"] = "hash"
os.environ["EMBEDDING_DIMENSION"] = "128"
os.environ["LLM_PROVIDER"] = "retrieval_only"
os.environ["VECTOR_INDEX_PATH"] = str(_TEST_ROOT / "test.index")
os.environ["VECTOR_METADATA_PATH"] = str(_TEST_ROOT / "metadata.json")
os.environ["VECTOR_NUMPY_PATH"] = str(_TEST_ROOT / "vectors.npz")
os.environ["KNOWLEDGE_BASE_PATH"] = str(_TEST_ROOT / "knowledge")
os.environ["RETRIEVAL_MIN_SCORE"] = "0.0"

import pytest
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.main import app


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    """Recreate all database tables before each test."""

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Return a FastAPI test client with lifespan support."""

    with TestClient(app) as test_client:
        yield test_client
