"""Unit tests for grounded prompt construction."""

from app.schemas.chat import SourceReference
from app.services.prompt_builder import PromptBuilder


def test_prompt_contains_question_source_and_safety_rules() -> None:
    source = SourceReference(
        document="Admission Policy",
        score=0.9,
        content="Patients should bring a photo identity document.",
    )
    prompt = PromptBuilder().build("What should I bring?", [source])
    assert "What should I bring?" in prompt
    assert "Admission Policy" in prompt
    assert "Do not diagnose" in prompt
    assert "untrusted data" in prompt
