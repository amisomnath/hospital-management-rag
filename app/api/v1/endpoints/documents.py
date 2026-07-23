"""Knowledge-base document endpoints."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.deps import DatabaseSession
from app.core.config import get_settings
from app.crud.knowledge_document import list_documents
from app.models.knowledge_document import KnowledgeDocument
from app.schemas.document import DocumentRead, IngestionResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/documents", tags=["Knowledge Documents"])


@router.get("", response_model=list[DocumentRead])
def read_documents(db: DatabaseSession) -> list[KnowledgeDocument]:
    """List files registered in the knowledge base."""

    return list_documents(db)


@router.post(
    "/upload",
    response_model=IngestionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    db: DatabaseSession, file: Annotated[UploadFile, File()]
) -> IngestionResponse:
    """Save and ingest a TXT, Markdown or PDF knowledge document."""

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".txt", ".md", ".pdf"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only TXT, Markdown and PDF files are supported",
        )

    settings = get_settings()
    settings.knowledge_base_path.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "uploaded_document.txt").name
    destination = settings.knowledge_base_path / safe_name
    destination.write_bytes(await file.read())

    try:
        result = RAGService().ingest_file(db, destination)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return IngestionResponse(**result)
