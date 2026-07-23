"""Document chunking utilities."""

import re
from dataclasses import dataclass


@dataclass(slots=True)
class TextChunk:
    """One overlapping chunk produced from a source document."""

    index: int
    content: str
    section: str | None = None
    page_number: int | None = None


def _normalise_whitespace(text: str) -> str:
    """Collapse repeated whitespace while keeping readable paragraphs."""

    paragraphs = [
        re.sub(r"\s+", " ", paragraph).strip()
        for paragraph in re.split(r"\n\s*\n", text)
    ]
    return "\n\n".join(part for part in paragraphs if part)


def create_word_chunks(
    text: str, chunk_size: int = 220, overlap: int = 40
) -> list[TextChunk]:
    """Split text into overlapping word-based chunks.

    Word chunking is deliberately transparent for students. In a larger
    system this module can be replaced by token-aware or semantic chunking
    without changing the rest of the RAG pipeline.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if overlap < 0:
        raise ValueError("overlap cannot be negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    normalised = _normalise_whitespace(text)
    words = normalised.split()
    if not words:
        return []

    step = chunk_size - overlap
    chunks: list[TextChunk] = []
    for index, start in enumerate(range(0, len(words), step)):
        content = " ".join(words[start : start + chunk_size]).strip()
        if content:
            chunks.append(TextChunk(index=index, content=content))
    return chunks
