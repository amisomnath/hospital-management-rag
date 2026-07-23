"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine

settings = get_settings()
configure_logging(settings.debug)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Prepare local directories and development database tables."""

    del app
    settings.knowledge_base_path.mkdir(parents=True, exist_ok=True)
    settings.vector_index_path.parent.mkdir(parents=True, exist_ok=True)
    # Alembic should manage production schemas. create_all keeps the classroom
    # SQLite setup immediately runnable.
    if settings.app_env in {"development", "testing"}:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Hospital management API and medical-only RAG chatbot with WebSocket support."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)

static_directory = Path("static")
static_directory.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_directory), name="static")


@app.get("/", include_in_schema=False)
def chat_page() -> FileResponse:
    """Serve the demonstration browser WebSocket client."""

    return FileResponse(static_directory / "chat.html")
