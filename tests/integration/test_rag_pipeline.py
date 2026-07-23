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


def test_unchanged_document_is_not_chunked_twice(tmp_path: Path) -> None:
    document = tmp_path / "policy.txt"
    document.write_text("The approved hospital policy text.", encoding="utf-8")

    with SessionLocal() as db:
        first = RAGService().ingest_file(db, document)
        second = RAGService().ingest_file(db, document)

    assert first["chunks_created"] == 1
    assert second["chunks_created"] == 0
    assert second["vectors_stored"] == 1


def test_same_content_at_another_path_is_deduplicated(tmp_path: Path) -> None:
    first_path = tmp_path / "policy.md"
    duplicate_path = tmp_path / "uploaded_policy.md"
    content = "Approved policy content that must be indexed only once."
    first_path.write_text(content, encoding="utf-8")
    duplicate_path.write_text(content, encoding="utf-8")

    with SessionLocal() as db:
        first = RAGService().ingest_file(db, first_path)
        duplicate = RAGService().ingest_file(db, duplicate_path)

    assert first["chunks_created"] == 1
    assert duplicate["chunks_created"] == 0
    assert duplicate["document"].id == first["document"].id


def test_directory_ingestion_is_recursive(tmp_path: Path) -> None:
    nested = tmp_path / "nested" / "medical"
    nested.mkdir(parents=True)
    (nested / "policy.md").write_text(
        "A nested approved medical policy.", encoding="utf-8"
    )

    with SessionLocal() as db:
        count = RAGService().ingest_directory(db, tmp_path)

    assert count == 1
