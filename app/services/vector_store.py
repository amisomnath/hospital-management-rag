"""Persistent dense-vector index with FAISS and NumPy fallback."""

import json
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from app.core.config import Settings, get_settings


@dataclass(slots=True)
class VectorSearchResult:
    """Metadata and score returned by vector similarity search."""

    score: float
    metadata: dict[str, Any]


class VectorStore:
    """Store normalised vectors and search them by cosine similarity.

    When ``faiss-cpu`` is installed, an ``IndexFlatIP`` index is persisted at
    ``hospital.index``. A NumPy copy is always persisted as a portable fallback.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._lock = threading.RLock()
        self._vectors: np.ndarray | None = None
        self._metadata: list[dict[str, Any]] | None = None
        self._faiss_index = None

    def _ensure_parent_directories(self) -> None:
        """Create index directories before writing files."""

        for path in (
            self.settings.vector_index_path,
            self.settings.vector_metadata_path,
            self.settings.vector_numpy_path,
        ):
            Path(path).parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _normalise(vectors: np.ndarray) -> np.ndarray:
        """L2-normalise vectors so inner product equals cosine similarity."""

        vectors = np.asarray(vectors, dtype=np.float32)
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vectors / norms

    def rebuild(self, vectors: np.ndarray, metadata: list[dict[str, Any]]) -> None:
        """Replace the complete index and persist it atomically enough for MVP use."""

        vectors = self._normalise(vectors)
        if len(vectors) != len(metadata):
            raise ValueError("Each vector must have exactly one metadata record")

        with self._lock:
            self._ensure_parent_directories()
            np.savez_compressed(self.settings.vector_numpy_path, vectors=vectors)
            self.settings.vector_metadata_path.write_text(
                json.dumps(metadata, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

            self._faiss_index = None
            try:
                import faiss

                index = faiss.IndexFlatIP(vectors.shape[1])
                if len(vectors):
                    index.add(vectors)
                faiss.write_index(index, str(self.settings.vector_index_path))
                self._faiss_index = index
            except ImportError:
                # NumPy search remains fully functional for smaller projects.
                Path(self.settings.vector_index_path).write_text(
                    "FAISS is not installed; NumPy fallback is active.\n",
                    encoding="utf-8",
                )

            self._vectors = vectors
            self._metadata = metadata

    def _load(self) -> None:
        """Load vectors and metadata lazily from persistent storage."""

        with self._lock:
            if self._vectors is not None and self._metadata is not None:
                return
            if not self.settings.vector_numpy_path.exists():
                self._vectors = np.empty((0, 0), dtype=np.float32)
                self._metadata = []
                return

            archive = np.load(self.settings.vector_numpy_path)
            self._vectors = np.asarray(archive["vectors"], dtype=np.float32)
            self._metadata = json.loads(
                self.settings.vector_metadata_path.read_text(encoding="utf-8")
            )

            try:
                import faiss

                if self.settings.vector_index_path.exists():
                    self._faiss_index = faiss.read_index(
                        str(self.settings.vector_index_path)
                    )
            except (ImportError, RuntimeError):
                self._faiss_index = None

    def search(
        self, query_vector: np.ndarray, top_k: int = 4
    ) -> list[VectorSearchResult]:
        """Return the highest-scoring nearest chunks."""

        self._load()
        assert self._vectors is not None
        assert self._metadata is not None

        if len(self._metadata) == 0:
            return []

        query = self._normalise(np.asarray(query_vector, dtype=np.float32))[0]
        limit = min(max(top_k, 1), len(self._metadata))

        if self._faiss_index is not None:
            scores, positions = self._faiss_index.search(query.reshape(1, -1), limit)
            pairs = zip(positions[0].tolist(), scores[0].tolist(), strict=True)
        else:
            scores = self._vectors @ query
            positions = np.argsort(scores)[::-1][:limit]
            pairs = ((int(position), float(scores[position])) for position in positions)

        results = []
        for position, score in pairs:
            if position < 0:
                continue
            results.append(
                VectorSearchResult(
                    score=float(score), metadata=self._metadata[position]
                )
            )
        return results

    def clear_memory_cache(self) -> None:
        """Force the next search to reload files from disk."""

        with self._lock:
            self._vectors = None
            self._metadata = None
            self._faiss_index = None
