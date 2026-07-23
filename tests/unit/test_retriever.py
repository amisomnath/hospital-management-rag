"""Unit test for deterministic embedding and vector retrieval."""

from pathlib import Path

from app.core.config import Settings
from app.services.embedding import EmbeddingService
from app.services.retriever import Retriever
from app.services.vector_store import VectorStore


def test_retriever_finds_password_document(tmp_path: Path) -> None:
    settings = Settings(
        app_env="testing",
        embedding_backend="hash",
        embedding_dimension=128,
        retrieval_min_score=0.0,
        vector_index_path=tmp_path / "test.index",
        vector_metadata_path=tmp_path / "metadata.json",
        vector_numpy_path=tmp_path / "vectors.npz",
    )
    embedding = EmbeddingService(settings)
    store = VectorStore(settings)
    texts = [
        "Patients can book a doctor appointment at the appointment desk.",
        "Visitors may enter the general ward during visiting hours.",
    ]
    store.rebuild(
        embedding.encode_documents(texts),
        [
            {"document": "Appointment Guide", "content": texts[0]},
            {"document": "Visiting Hours", "content": texts[1]},
        ],
    )
    results = Retriever(settings, embedding, store).retrieve(
        "How can a patient book an appointment?", top_k=1
    )
    assert results
    assert results[0].document == "Appointment Guide"
