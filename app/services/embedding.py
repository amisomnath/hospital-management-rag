"""Hugging Face and deterministic test embedding backends."""

import hashlib
import re
import threading
from collections.abc import Iterable
from typing import Any

import numpy as np

from app.core.config import Settings, get_settings


class EmbeddingService:
    """Generate normalised document and query embeddings.

    Production/default mode uses a Hugging Face SentenceTransformer. The
    ``hash`` backend is deterministic, dependency-light and intended for tests
    and classroom demonstrations where model downloads are unavailable.
    """

    _model_cache: dict[tuple[str, str | None], Any] = {}
    _cache_lock = threading.Lock()

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def dimension(self) -> int:
        """Return the configured output-vector dimension."""

        if self.settings.embedding_backend == "hash":
            return self.settings.embedding_dimension
        model = self._get_sentence_transformer()
        dimension = model.get_sentence_embedding_dimension()
        if dimension is None:
            raise RuntimeError("The embedding model did not report its dimension")
        return int(dimension)

    def _get_sentence_transformer(self) -> Any:
        """Load and cache the selected SentenceTransformer model."""

        key = (self.settings.embedding_model, self.settings.embedding_device)
        if key in self._model_cache:
            return self._model_cache[key]

        with self._cache_lock:
            if key in self._model_cache:
                return self._model_cache[key]
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError(
                    "sentence-transformers is required for the default embedding "
                    "backend. Install requirements.txt or set "
                    "EMBEDDING_BACKEND=hash for tests."
                ) from exc
            model = SentenceTransformer(
                self.settings.embedding_model,
                device=self.settings.embedding_device,
            )
            self._model_cache[key] = model
            return model

    def _hash_encode(self, texts: Iterable[str]) -> np.ndarray:
        """Create stable bag-of-token hash embeddings without model downloads."""

        dimension = self.settings.embedding_dimension
        vectors: list[np.ndarray] = []
        for text in texts:
            vector = np.zeros(dimension, dtype=np.float32)
            for token in re.findall(r"[a-zA-Z0-9]+", text.lower()):
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:4], "big") % dimension
                sign = 1.0 if digest[4] % 2 == 0 else -1.0
                vector[index] += sign
            norm = float(np.linalg.norm(vector))
            if norm:
                vector /= norm
            vectors.append(vector)
        if not vectors:
            return np.empty((0, dimension), dtype=np.float32)
        return np.vstack(vectors).astype(np.float32)

    def encode_documents(self, texts: list[str]) -> np.ndarray:
        """Encode knowledge-base chunks as normalised float32 vectors."""

        if self.settings.embedding_backend == "hash":
            return self._hash_encode(texts)

        model = self._get_sentence_transformer()
        encoder = getattr(model, "encode_document", model.encode)
        vectors = encoder(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype=np.float32)

    def encode_query(self, text: str) -> np.ndarray:
        """Encode one user question using the same embedding space."""

        if self.settings.embedding_backend == "hash":
            return self._hash_encode([text])[0]

        model = self._get_sentence_transformer()
        encoder = getattr(model, "encode_query", model.encode)
        vector = encoder(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vector, dtype=np.float32)
