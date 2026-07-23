"""No-key retrieval-only answer provider."""

from app.llm.base import GenerationResult, LLMProvider


class RetrievalOnlyProvider(LLMProvider):
    """Return retrieved evidence without calling a generative model."""

    name = "retrieval_only"

    async def generate(
        self, prompt: str, context_chunks: list[str]
    ) -> GenerationResult:
        """Assemble a transparent answer from the retrieved passages."""

        del prompt
        unique_chunks = list(dict.fromkeys(chunk.strip() for chunk in context_chunks))
        bullets = "\n".join(f"- {chunk}" for chunk in unique_chunks if chunk)
        text = (
            "Based on the approved hospital knowledge base:\n" + bullets
            if bullets
            else "The approved knowledge base does not contain enough information."
        )
        return GenerationResult(text=text, provider=self.name)
