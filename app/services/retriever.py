"""Question-to-document retrieval service."""

import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.schemas.chat import SourceReference
from app.services.embedding import EmbeddingService
from app.services.vector_store import VectorStore


class Retriever:
    """Embed a question and retrieve relevant approved chunks."""

    def __init__(
        self,
        settings: Settings | None = None,
        embedding_service: EmbeddingService | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.embedding_service = embedding_service or EmbeddingService(self.settings)
        self.vector_store = vector_store or VectorStore(self.settings)

    def retrieve(
        self,
        question: str,
        top_k: int | None = None,
        db: Session | None = None,
    ) -> list[SourceReference]:
        """Return source chunks that pass the configured similarity threshold."""

        query_vector = self.embedding_service.encode_query(question)
        is_postgres = (
            db is not None
            and db.bind is not None
            and db.bind.dialect.name == "postgresql"
        )
        if is_postgres:
            assert db is not None
            return self._retrieve_pgvector(
                db, query_vector.tolist(), top_k or self.settings.retrieval_top_k
            )

        raw_results = self.vector_store.search(
            query_vector, top_k=top_k or self.settings.retrieval_top_k
        )

        sources: list[SourceReference] = []
        for result in raw_results:
            if result.score < self.settings.retrieval_min_score:
                continue
            metadata = result.metadata
            sources.append(
                SourceReference(
                    document_id=metadata.get("document_id"),
                    document=metadata.get("document", "Unknown document"),
                    chunk_id=metadata.get("chunk_id"),
                    section=metadata.get("section"),
                    page_number=metadata.get("page_number"),
                    score=result.score,
                    content=metadata.get("content", ""),
                )
            )
        return sources

    def _retrieve_pgvector(
        self, db: Session, query_vector: list[float], top_k: int
    ) -> list[SourceReference]:
        """Search PostgreSQL with pgvector cosine distance."""

        statement = text(
            """
            SELECT
                kd.id AS document_id,
                kd.title AS document,
                kc.id AS chunk_id,
                kc.section,
                kc.page_number,
                kc.content,
                1 - (kc.embedding <=> CAST(:query_vector AS vector)) AS score
            FROM knowledge_chunks AS kc
            JOIN knowledge_documents AS kd ON kd.id = kc.document_id
            WHERE kd.is_active IS TRUE
              AND kc.embedding IS NOT NULL
              AND 1 - (kc.embedding <=> CAST(:query_vector AS vector)) >= :min_score
            ORDER BY kc.embedding <=> CAST(:query_vector AS vector)
            LIMIT :top_k
            """
        )
        rows = db.execute(
            statement,
            {
                "query_vector": json.dumps(query_vector),
                "min_score": self.settings.retrieval_min_score,
                "top_k": top_k,
            },
        ).mappings()
        return [
            SourceReference(
                document_id=row["document_id"],
                document=row["document"],
                chunk_id=row["chunk_id"],
                section=row["section"],
                page_number=row["page_number"],
                score=float(row["score"]),
                content=row["content"],
            )
            for row in rows
        ]
