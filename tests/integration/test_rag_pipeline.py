"""End-to-end test for ingestion and retrieval."""

from pathlib import Path

from app.db.session import SessionLocal
from app.services.rag_service import RAGService


def test_ingestion_and_retrieval(tmp_path: Path) -> None:
    document = tmp_path / "admission.txt"
    document.write_text(
        "Patients should bring a government photo identity document for admission.",
        encoding="utf-8",
    )

    with SessionLocal() as db:
        result = RAGService().ingest_file(db, document)
        assert result["chunks_created"] == 1

    sources = RAGService().retrieve("Which identity document is needed for admission?")
    assert sources
    assert "identity" in sources[0].content.lower()


def test_directory_ingestion_rebuilds_multiple_documents_once(tmp_path: Path) -> None:
    (tmp_path / "admission.txt").write_text(
        "Patients should bring an identity document for admission.",
        encoding="utf-8",
    )
    (tmp_path / "visiting.txt").write_text(
        "General ward visiting hours are from four to six in the evening.",
        encoding="utf-8",
    )

    with SessionLocal() as db:
        count = RAGService().ingest_directory(db, tmp_path)
        assert count == 2

    sources = RAGService().retrieve("What identity is needed for admission?")
    assert sources
    assert "identity" in sources[0].content.lower()
