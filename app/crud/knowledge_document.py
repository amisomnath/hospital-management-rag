"""Knowledge-document CRUD functions."""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument


def list_documents(db: Session) -> list[KnowledgeDocument]:
    """Return active and inactive knowledge documents."""

    statement = select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())
    return list(db.scalars(statement).all())


def get_document_by_path(db: Session, source_path: str) -> KnowledgeDocument | None:
    """Find a document using its stored source path."""

    return db.scalar(
        select(KnowledgeDocument).where(KnowledgeDocument.source_path == source_path)
    )


def get_document_by_checksum(
    db: Session, checksum: str
) -> KnowledgeDocument | None:
    """Find an active document with identical source bytes."""

    return db.scalar(
        select(KnowledgeDocument).where(
            KnowledgeDocument.checksum == checksum,
            KnowledgeDocument.is_active.is_(True),
        )
    )


def delete_document_chunks(db: Session, document_id: str) -> None:
    """Delete all chunks before re-ingesting a changed document."""

    db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id))
