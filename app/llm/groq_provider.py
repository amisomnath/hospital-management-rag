"""Groq hosted chat-completion provider."""

from app.core.config import Settings, get_settings
from app.llm.base import GenerationResult, LLMProvider


class GroqProvider(LLMProvider):
    """Generate an answer with Groq's asynchronous Python client."""

    name = "groq"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        if not self.settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER=groq")

    async def generate(
        self, prompt: str, context_chunks: list[str]
    ) -> GenerationResult:
        """Send the grounded prompt to the configured Groq model."""

        del context_chunks
        try:
            from groq import AsyncGroq
        except ImportError as exc:
            raise RuntimeError("The groq package is required for Groq mode.") from exc

        client = AsyncGroq(api_key=self.settings.groq_api_key)
        completion = await client.chat.completions.create(
            model=self.settings.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=512,
        )
        text = completion.choices[0].message.content or ""
        return GenerationResult(text=text.strip(), provider=self.name)
