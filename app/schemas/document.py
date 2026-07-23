"""Knowledge-document schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    """Knowledge document returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    title: str
    content_type: str
    source_path: str
    checksum: str
    is_active: bool
    created_at: datetime


class IngestionResponse(BaseModel):
    """Summary produced after document ingestion."""

    document: DocumentRead
    chunks_created: int
    vectors_stored: int


class BulkIngestionResponse(BaseModel):
    """Summary produced after one multi-file ingestion request."""

    files_received: int
    documents_indexed: int
    duplicates_skipped: int
    chunks_created: int
    vectors_stored: int
    documents: list[DocumentRead]
