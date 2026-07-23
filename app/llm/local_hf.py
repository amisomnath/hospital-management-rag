"""Local Hugging Face text-to-text generation provider."""

import asyncio
import threading
from typing import Any

from app.core.config import Settings, get_settings
from app.llm.base import GenerationResult, LLMProvider


class LocalHuggingFaceProvider(LLMProvider):
    """Run an instruction-tuned Hugging Face model on the local machine."""

    name = "local_hf"
    _models: dict[tuple[str, int], tuple[Any, Any, Any]] = {}
    _lock = threading.Lock()

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _get_model(self) -> tuple[Any, Any, Any]:
        """Load and cache tokenizer/model/device on first use."""

        key = (self.settings.local_llm_model, self.settings.local_llm_device)
        if key in self._models:
            return self._models[key]
        with self._lock:
            if key in self._models:
                return self._models[key]
            try:
                import torch
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            except ImportError as exc:
                raise RuntimeError(
                    "transformers and torch are required for LOCAL_HF mode."
                ) from exc

            if self.settings.local_llm_device >= 0:
                if not torch.cuda.is_available():
                    raise RuntimeError(
                        "LOCAL_LLM_DEVICE requests CUDA, but PyTorch cannot access it."
                    )
                device = torch.device(
                    f"cuda:{self.settings.local_llm_device}"
                )
            else:
                device = torch.device("cpu")

            tokenizer = AutoTokenizer.from_pretrained(
                self.settings.local_llm_model
            )
            model = AutoModelForSeq2SeqLM.from_pretrained(
                self.settings.local_llm_model
            ).to(device)
            model.eval()
            self._models[key] = (tokenizer, model, device)
            return self._models[key]

    def _generate_sync(self, prompt: str) -> str:
        """Run blocking model inference outside the async event loop."""

        import torch

        tokenizer, model, device = self._get_model()
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=1024,
        ).to(device)
        with torch.inference_mode():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=self.settings.local_llm_max_new_tokens,
                do_sample=False,
            )
        return str(
            tokenizer.decode(output_ids[0], skip_special_tokens=True)
        ).strip()

    async def generate(
        self, prompt: str, context_chunks: list[str]
    ) -> GenerationResult:
        """Generate a grounded answer using a local Hugging Face model."""

        del context_chunks
        text = await asyncio.to_thread(self._generate_sync, prompt)
        return GenerationResult(text=text, provider=self.name)
