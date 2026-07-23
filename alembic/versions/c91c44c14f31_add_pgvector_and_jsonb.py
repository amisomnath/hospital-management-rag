"""add pgvector embeddings and PostgreSQL JSONB

Revision ID: c91c44c14f31
Revises: 7b3be7e8e60b
Create Date: 2026-07-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "c91c44c14f31"
down_revision: str | Sequence[str] | None = "7b3be7e8e60b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Enable pgvector, add embeddings and use JSONB for source metadata."""

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        op.add_column(
            "knowledge_chunks",
            sa.Column("embedding", Vector(384), nullable=True),
        )
        op.alter_column(
            "chat_messages",
            "sources",
            existing_type=sa.JSON(),
            type_=postgresql.JSONB(astext_type=sa.Text()),
            existing_nullable=True,
            postgresql_using="sources::jsonb",
        )
    else:
        # SQLite remains supported for the automated test fallback.
        op.add_column(
            "knowledge_chunks",
            sa.Column("embedding", sa.JSON(), nullable=True),
        )


def downgrade() -> None:
    """Remove stored embeddings and restore generic JSON."""

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.alter_column(
            "chat_messages",
            "sources",
            existing_type=postgresql.JSONB(astext_type=sa.Text()),
            type_=sa.JSON(),
            existing_nullable=True,
            postgresql_using="sources::json",
        )
    op.drop_column("knowledge_chunks", "embedding")
