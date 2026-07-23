"""Question-to-document retrieval service."""

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
        self, question: str, top_k: int | None = None
    ) -> list[SourceReference]:
        """Return source chunks that pass the configured similarity threshold."""

        query_vector = self.embedding_service.encode_query(question)
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
