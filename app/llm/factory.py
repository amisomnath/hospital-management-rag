"""Select an answer provider from application configuration."""

import logging

from app.core.config import Settings, get_settings
from app.llm.base import LLMProvider
from app.llm.groq_provider import GroqProvider
from app.llm.local_hf import LocalHuggingFaceProvider
from app.llm.retrieval_only import RetrievalOnlyProvider

logger = logging.getLogger(__name__)


def create_llm_provider(settings: Settings | None = None) -> LLMProvider:
    """Return the configured provider with a safe no-key fallback."""

    settings = settings or get_settings()
    if settings.llm_provider == "local_hf":
        return LocalHuggingFaceProvider(settings)
    if settings.llm_provider == "groq":
        if not settings.groq_api_key:
            logger.warning(
                "Groq mode requested without GROQ_API_KEY; using retrieval-only."
            )
            return RetrievalOnlyProvider()
        return GroqProvider(settings)
    return RetrievalOnlyProvider()
