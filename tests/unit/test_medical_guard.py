"""Unit tests for chatbot scope rules."""

from app.services.medical_guard import MedicalGuard


def test_greeting_is_allowed() -> None:
    guard = MedicalGuard()
    result = guard.classify("Hello")
    assert result.allowed is True
    assert result.category == "greeting"


def test_medical_question_is_allowed() -> None:
    guard = MedicalGuard()
    result = guard.classify("What is blood pressure?")
    assert result.allowed is True
    assert result.category == "medical"


def test_unrelated_question_is_rejected() -> None:
    guard = MedicalGuard()
    result = guard.classify("Write a Python sorting program")
    assert result.allowed is False
