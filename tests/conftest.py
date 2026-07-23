"""Shared isolated application fixtures."""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

_TEST_ROOT = Path(tempfile.mkdtemp(prefix="hospital-rag-tests-"))
os.environ["APP_ENV"] = "testing"
os.environ["APP_DEBUG"] = "false"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_ROOT / 'test.db'}"
os.environ["EMBEDDING_BACKEND"] = "hash"
os.environ["EMBEDDING_DIMENSION"] = "128"
os.environ["LLM_PROVIDER"] = "retrieval_only"
os.environ["VECTOR_INDEX_PATH"] = str(_TEST_ROOT / "test.index")
os.environ["VECTOR_METADATA_PATH"] = str(_TEST_ROOT / "metadata.json")
os.environ["VECTOR_NUMPY_PATH"] = str(_TEST_ROOT / "vectors.npz")
os.environ["KNOWLEDGE_BASE_PATH"] = str(_TEST_ROOT / "knowledge")
os.environ["KNOWLEDGE_UPLOAD_PATH"] = str(_TEST_ROOT / "knowledge" / "uploads")
os.environ["RETRIEVAL_MIN_SCORE"] = "0.0"

import pytest
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.main import app
from app.models.user import User


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


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    """Register/login a patient and return a Bearer authorization header."""

    credentials = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "test-password-123",
    }
    response = client.post("/api/v1/auth/register", json=credentials)
    assert response.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
def staff_auth_headers(auth_headers: dict[str, str]) -> dict[str, str]:
    """Promote the fixture user so staff-only ingestion APIs can be tested."""

    with SessionLocal() as db:
        user = db.query(User).filter(User.email == "test@example.com").one()
        user.role = "staff"
        db.commit()
    return auth_headers
