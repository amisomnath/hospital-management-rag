"""Scope guard that permits greetings and medical/hospital questions."""

import re
from dataclasses import dataclass


@dataclass(slots=True)
class MedicalScopeResult:
    """Decision produced by the medical-scope guard."""

    category: str
    allowed: bool
    confidence: float
    reason: str


class MedicalGuard:
    """Apply transparent rule-based medical-domain validation.

    This is a scope control, not a diagnosis model. Retrieval confidence is
    accepted as supporting evidence because approved hospital documents may use
    terms not present in the keyword list.
    """

    greetings = {
        "hi",
        "hello",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
        "how are you",
        "namaste",
    }

    medical_terms = {
        "admission",
        "allergy",
        "ambulance",
        "appointment",
        "asthma",
        "blood",
        "blood pressure",
        "cardiology",
        "clinic",
        "cough",
        "dehydration",
        "diabetes",
        "diagnosis",
        "diet",
        "discharge",
        "doctor",
        "emergency",
        "fever",
        "headache",
        "health",
        "heart",
        "hospital",
        "hypertension",
        "infection",
        "injury",
        "medicine",
        "medication",
        "nurse",
        "pain",
        "patient",
        "pharmacy",
        "prescription",
        "symptom",
        "surgery",
        "test",
        "treatment",
        "vaccine",
        "visitor",
        "visiting hours",
        "ward",
        "x-ray",
    }

    def is_greeting(self, message: str) -> bool:
        """Return True when the normalised message is a simple greeting."""

        normalised = re.sub(r"[^a-zA-Z ]", "", message.lower()).strip()
        return normalised in self.greetings

    def classify(
        self, message: str, retrieval_confidence: float = 0.0
    ) -> MedicalScopeResult:
        """Allow a message when terms or approved retrieval support its scope."""

        if self.is_greeting(message):
            return MedicalScopeResult("greeting", True, 1.0, "Known greeting")

        lowered = message.lower()
        matched = [term for term in self.medical_terms if term in lowered]
        if matched:
            confidence = min(0.65 + len(matched) * 0.05, 0.95)
            return MedicalScopeResult(
                "medical", True, confidence, f"Medical terms: {', '.join(matched[:4])}"
            )

        if retrieval_confidence >= 0.55:
            return MedicalScopeResult(
                "hospital_knowledge",
                True,
                retrieval_confidence,
                "Strong match with approved hospital knowledge",
            )

        return MedicalScopeResult(
            "unsupported",
            False,
            1.0 - retrieval_confidence,
            "No reliable medical or hospital signal",
        )
