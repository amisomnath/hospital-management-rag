"""CLI command for ingesting approved hospital knowledge files."""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.services.rag_service import RAGService


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""

    parser = argparse.ArgumentParser(
        description="Ingest hospital knowledge documents and rebuild vectors."
    )
    parser.add_argument(
        "--directory",
        type=Path,
        default=None,
        help="Directory tree containing TXT, Markdown, PDF or DOCX files.",
    )
    parser.add_argument(
        "--rebuild-only",
        action="store_true",
        help="Rebuild vectors from chunks already stored in the database.",
    )
    return parser.parse_args()


def main() -> None:
    """Run ingestion or index rebuilding."""

    args = parse_args()
    settings = get_settings()
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
    service = RAGService(settings)

    with SessionLocal() as db:
        if args.rebuild_only:
            count = service.rebuild_index(db)
            print(f"Rebuilt vector index with {count} chunks.")
            return

        directory = (args.directory or settings.knowledge_base_path).resolve()
        if not directory.exists():
            raise SystemExit(f"Directory does not exist: {directory}")
        count = service.ingest_directory(db, directory)
        print(
            f"Scanned {count} supported files from {directory}; "
            "checksum duplicates were skipped and the index was rebuilt."
        )


if __name__ == "__main__":
    main()
