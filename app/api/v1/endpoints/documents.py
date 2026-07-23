"""Knowledge-base document endpoints."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.deps import DatabaseSession, StaffUser
from app.core.config import get_settings
from app.crud.knowledge_document import list_documents
from app.models.knowledge_document import KnowledgeDocument
from app.schemas.document import (
    BulkIngestionResponse,
    DocumentRead,
    IngestionResponse,
)
from app.services.document_loader import SUPPORTED_EXTENSIONS
from app.services.rag_service import RAGService

router = APIRouter(prefix="/documents", tags=["Knowledge Documents"])


async def _read_upload(file: UploadFile) -> tuple[str, bytes]:
    """Validate one uploaded file and return its safe name and bytes."""

    settings = get_settings()
    safe_name = Path(file.filename or "uploaded_document.txt").name
    suffix = Path(safe_name).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"{safe_name}: only TXT, Markdown, PDF and DOCX files "
                "are supported"
            ),
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{safe_name}: uploaded file is empty",
        )
    if len(content) > settings.document_max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"{safe_name}: maximum upload size is "
                f"{settings.document_max_upload_mb} MB per file"
            ),
        )
    return safe_name, content


def _remove_duplicate_upload(destination: Path, source_path: str) -> None:
    """Delete a just-uploaded byte duplicate that reused an existing document."""

    if str(destination.resolve()) != source_path:
        destination.unlink(missing_ok=True)


@router.get("", response_model=list[DocumentRead])
def read_documents(db: DatabaseSession, _: StaffUser) -> list[KnowledgeDocument]:
    """List files registered in the knowledge base."""

    return list_documents(db)


@router.post(
    "/upload",
    response_model=IngestionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    db: DatabaseSession, _: StaffUser, file: Annotated[UploadFile, File()]
) -> IngestionResponse:
    """Save and ingest a TXT, Markdown or PDF knowledge document."""

    settings = get_settings()
    safe_name, content = await _read_upload(file)
    settings.knowledge_upload_path.mkdir(parents=True, exist_ok=True)
    destination = settings.knowledge_upload_path / safe_name
    destination.write_bytes(content)

    try:
        result = RAGService().ingest_file(db, destination)
    except (ValueError, RuntimeError) as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _remove_duplicate_upload(destination, result["document"].source_path)
    return IngestionResponse(**result)


@router.post(
    "/upload/bulk",
    response_model=BulkIngestionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_documents_bulk(
    db: DatabaseSession,
    _: StaffUser,
    files: Annotated[list[UploadFile], File(description="Knowledge files")],
) -> BulkIngestionResponse:
    """Upload many files and rebuild the vector index only once."""

    settings = get_settings()
    if not files:
        raise HTTPException(status_code=400, detail="Select at least one file")
    if len(files) > settings.document_max_batch_files:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Maximum batch size is {settings.document_max_batch_files} files"
            ),
        )

    uploads = [await _read_upload(file) for file in files]
    names = [name.casefold() for name, _content in uploads]
    if len(names) != len(set(names)):
        raise HTTPException(
            status_code=400,
            detail="A batch cannot contain the same filename more than once",
        )

    settings.knowledge_upload_path.mkdir(parents=True, exist_ok=True)
    service = RAGService()
    results: list[dict] = []
    try:
        for safe_name, content in uploads:
            destination = settings.knowledge_upload_path / safe_name
            destination.write_bytes(content)
            result = service.ingest_file(db, destination, rebuild_index=False)
            _remove_duplicate_upload(destination, result["document"].source_path)
            results.append(result)
        vectors_stored = service.rebuild_index(db)
    except (ValueError, RuntimeError) as exc:
        # Successful earlier files committed their SQL chunks. Rebuild before
        # returning so PostgreSQL vectors never remain stale after a partial batch.
        service.rebuild_index(db)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    documents_indexed = sum(
        result["chunks_created"] > 0 for result in results
    )
    return BulkIngestionResponse(
        files_received=len(files),
        documents_indexed=documents_indexed,
        duplicates_skipped=len(files) - documents_indexed,
        chunks_created=sum(result["chunks_created"] for result in results),
        vectors_stored=vectors_stored,
        documents=[result["document"] for result in results],
    )
