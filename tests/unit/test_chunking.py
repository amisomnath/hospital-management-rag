"""Unit tests for word chunking."""

import pytest

from app.services.chunking import create_word_chunks


def test_chunking_creates_overlap() -> None:
    """The next chunk repeats the configured number of words."""

    text = " ".join(f"word{number}" for number in range(20))
    chunks = create_word_chunks(text, chunk_size=10, overlap=2)
    assert len(chunks) == 3
    first_words = chunks[0].content.split()
    second_words = chunks[1].content.split()
    assert first_words[-2:] == second_words[:2]


def test_chunking_rejects_invalid_overlap() -> None:
    """Overlap must be smaller than the chunk size."""

    with pytest.raises(ValueError):
        create_word_chunks("some text", chunk_size=10, overlap=10)
