"""Conservative detection of possible medical-emergency language."""

import re
from dataclasses import dataclass


@dataclass(slots=True)
class EmergencyResult:
    """Possible-emergency classification result."""

    detected: bool
    reason: str | None = None


class EmergencyGuard:
    """Detect a small set of high-risk phrases and stop normal generation."""

    patterns = {
        "breathing difficulty": (
            r"(cannot|can't|unable to|difficulty)\s+(breathe|breathing)"
        ),
        "chest pain": r"(severe\s+)?chest\s+pain",
        "unconsciousness": r"(unconscious|not waking|won't wake)",
        "heavy bleeding": r"(heavy|severe|uncontrolled)\s+bleeding",
        "possible stroke": r"(face droop|slurred speech|one-sided weakness)",
        "self-harm emergency": r"(overdose|took too many pills)",
    }

    emergency_message = (
        "Your message may describe a medical emergency. Contact your local "
        "emergency service or go to the nearest emergency department now. "
        "Do not rely on this chatbot for urgent medical care."
    )

    def check(self, message: str) -> EmergencyResult:
        """Return the first detected emergency pattern, if any."""

        for reason, pattern in self.patterns.items():
            if re.search(pattern, message, flags=re.IGNORECASE):
                return EmergencyResult(True, reason)
        return EmergencyResult(False)
