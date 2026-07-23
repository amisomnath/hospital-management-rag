"""Document ingestion, index rebuilding and retrieval orchestration."""

from pathlib import Path

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.crud.knowledge_document import (
    delete_document_chunks,
    get_document_by_checksum,
    get_document_by_path,
)
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument
from app.schemas.chat import SourceReference
from app.services.chunking import create_word_chunks
from app.services.document_loader import SUPPORTED_EXTENSIONS, load_document
from app.services.embedding import EmbeddingService
from app.services.retriever import Retriever
from app.services.vector_store import VectorStore


class RAGService:
    """Coordinate both ingestion-time and query-time RAG operations."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.embedding_service = EmbeddingService(self.settings)
        self.vector_store = VectorStore(self.settings)
        self.retriever = Retriever(
            self.settings, self.embedding_service, self.vector_store
        )

    def ingest_file(self, db: Session, path: Path, rebuild_index: bool = True) -> dict:
        """Load, chunk and persist one file, optionally rebuilding vectors."""

        loaded = load_document(path)
        source_path = str(loaded.path)
        document = get_document_by_path(db, source_path)
        duplicate = get_document_by_checksum(db, loaded.checksum)

        if (
            document is not None
            and document.is_active
            and document.checksum == loaded.checksum
            and document.chunks
        ):
            vector_count = db.scalar(
                select(func.count(KnowledgeChunk.id))
                .join(KnowledgeDocument)
                .where(KnowledgeDocument.is_active.is_(True))
            )
            return {
                "document": document,
                "chunks_created": 0,
                "vectors_stored": int(vector_count or 0),
            }
        if duplicate is not None and duplicate.id != getattr(document, "id", None):
            vector_count = db.scalar(
                select(func.count(KnowledgeChunk.id))
                .join(KnowledgeDocument)
                .where(KnowledgeDocument.is_active.is_(True))
            )
            return {
                "document": duplicate,
                "chunks_created": 0,
                "vectors_stored": int(vector_count or 0),
            }

        if document is None:
            document = KnowledgeDocument(
                filename=loaded.path.name,
                title=loaded.title,
                content_type=loaded.content_type,
                source_path=source_path,
                checksum=loaded.checksum,
            )
            db.add(document)
            db.flush()
        else:
            document.filename = loaded.path.name
            document.title = loaded.title
            document.content_type = loaded.content_type
            document.checksum = loaded.checksum
            document.is_active = True
            delete_document_chunks(db, document.id)

        chunks = create_word_chunks(
            loaded.text,
            chunk_size=self.settings.chunk_size,
            overlap=self.settings.chunk_overlap,
        )
        if not chunks:
            raise ValueError("The document did not produce any text chunks")

        for chunk in chunks:
            db.add(
                KnowledgeChunk(
                    document_id=document.id,
                    chunk_index=chunk.index,
                    content=chunk.content,
                    page_number=chunk.page_number,
                    section=chunk.section,
                )
            )
        db.commit()
        db.refresh(document)

        vectors_stored = self.rebuild_index(db) if rebuild_index else 0
        return {
            "document": document,
            "chunks_created": len(chunks),
            "vectors_stored": vectors_stored,
        }

    def ingest_directory(self, db: Session, directory: Path) -> int:
        """Ingest all supported files in a directory and return file count."""

        supported = [
            path
            for path in sorted(directory.rglob("*"))
            if path.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
        for path in supported:
            self.ingest_file(db, path, rebuild_index=False)
        if supported:
            self.rebuild_index(db)
        return len(supported)

    def rebuild_index(self, db: Session) -> int:
        """Re-encode every active chunk so vectors and metadata stay aligned."""

        statement = (
            select(KnowledgeChunk, KnowledgeDocument)
            .join(KnowledgeDocument)
            .where(KnowledgeDocument.is_active.is_(True))
            .order_by(KnowledgeDocument.id, KnowledgeChunk.chunk_index)
        )
        rows = db.execute(statement).all()

        if not rows:
            if db.bind is not None and db.bind.dialect.name == "postgresql":
                return 0
            import numpy as np

            self.vector_store.rebuild(
                np.empty((0, self.settings.embedding_dimension), dtype=np.float32),
                [],
            )
            return 0

        texts = [chunk.content for chunk, _document in rows]
        vectors = self.embedding_service.encode_documents(texts)

        # Clear old positions before assigning the rebuilt index. Without this
        # step, databases that enforce the unique vector_id constraint can see
        # temporary collisions while positions are being reordered.
        db.execute(update(KnowledgeChunk).values(vector_id=None))
        db.flush()

        metadata = []
        for vector_id, (chunk, document) in enumerate(rows):
            chunk.vector_id = vector_id
            chunk.embedding = vectors[vector_id].tolist()
            metadata.append(
                {
                    "vector_id": vector_id,
                    "document_id": document.id,
                    "document": document.title,
                    "chunk_id": chunk.id,
                    "section": chunk.section,
                    "page_number": chunk.page_number,
                    "content": chunk.content,
                }
            )
        db.commit()
        # PostgreSQL/pgvector is the production vector store. The local
        # NumPy/FAISS files remain a lightweight SQLite test/development fallback.
        if db.bind is None or db.bind.dialect.name != "postgresql":
            self.vector_store.rebuild(vectors, metadata)
        return len(metadata)

    def retrieve(
        self, question: str, db: Session | None = None
    ) -> list[SourceReference]:
        """Retrieve approved knowledge chunks for one question."""

        return self.retriever.retrieve(question, db=db)
