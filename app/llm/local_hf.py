"""Local Hugging Face text-to-text generation provider."""

import asyncio
import threading
from typing import Any

from app.core.config import Settings, get_settings
from app.llm.base import GenerationResult, LLMProvider


class LocalHuggingFaceProvider(LLMProvider):
    """Run an instruction-tuned Hugging Face model on the local machine."""

    name = "local_hf"
    _pipelines: dict[tuple[str, int], Any] = {}
    _lock = threading.Lock()

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _get_pipeline(self) -> Any:
        """Load and cache the text-to-text pipeline on first use."""

        key = (self.settings.local_llm_model, self.settings.local_llm_device)
        if key in self._pipelines:
            return self._pipelines[key]
        with self._lock:
            if key in self._pipelines:
                return self._pipelines[key]
            try:
                from transformers import pipeline
            except ImportError as exc:
                raise RuntimeError(
                    "transformers and torch are required for LOCAL_HF mode."
                ) from exc
            pipeline_factory: Any = pipeline
            generator = pipeline_factory(
                "text2text-generation",
                model=self.settings.local_llm_model,
                device=self.settings.local_llm_device,
            )
            self._pipelines[key] = generator
            return generator

    def _generate_sync(self, prompt: str) -> str:
        """Run blocking model inference outside the async event loop."""

        generator = self._get_pipeline()
        output = generator(
            prompt,
            max_new_tokens=self.settings.local_llm_max_new_tokens,
            do_sample=False,
        )
        return str(output[0]["generated_text"]).strip()

    async def generate(
        self, prompt: str, context_chunks: list[str]
    ) -> GenerationResult:
        """Generate a grounded answer using a local Hugging Face model."""

        del context_chunks
        text = await asyncio.to_thread(self._generate_sync, prompt)
        return GenerationResult(text=text, provider=self.name)
