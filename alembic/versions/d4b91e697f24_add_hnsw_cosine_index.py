"""add HNSW cosine index for knowledge embeddings

Revision ID: d4b91e697f24
Revises: c91c44c14f31
Create Date: 2026-07-23
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d4b91e697f24"
down_revision: str | Sequence[str] | None = "c91c44c14f31"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create an approximate nearest-neighbour cosine index in PostgreSQL."""

    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            """
            CREATE INDEX ix_knowledge_chunks_embedding_hnsw
            ON knowledge_chunks
            USING hnsw (embedding vector_cosine_ops)
            """
        )


def downgrade() -> None:
    """Remove the HNSW index."""

    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_embedding_hnsw")
