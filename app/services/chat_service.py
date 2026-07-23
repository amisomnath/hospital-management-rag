"""Medical chatbot business workflow."""

import logging

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.crud.chat import add_message, get_or_create_session
from app.llm.factory import create_llm_provider
from app.llm.retrieval_only import RetrievalOnlyProvider
from app.schemas.chat import ChatResponse
from app.services.emergency_guard import EmergencyGuard
from app.services.medical_guard import MedicalGuard
from app.services.prompt_builder import PromptBuilder
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)


class ChatService:
    """Validate scope, retrieve evidence and generate a safe response."""

    safety_notice = (
        "This chatbot provides general information and does not replace a "
        "qualified medical professional."
    )

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.medical_guard = MedicalGuard()
        self.emergency_guard = EmergencyGuard()
        self.rag_service = RAGService(self.settings)
        self.prompt_builder = PromptBuilder()

    def _persist_user_message(self, db: Session, session_id: str, message: str) -> None:
        if self.settings.save_chat_history:
            add_message(db, session_id, "user", message)

    def _persist_answer(
        self, db: Session, session_id: str, response: ChatResponse
    ) -> None:
        if self.settings.save_chat_history:
            add_message(
                db,
                session_id,
                "assistant",
                response.answer,
                provider=response.provider,
                sources=[source.model_dump() for source in response.sources],
            )

    async def process(
        self, db: Session, message: str, session_id: str | None = None
    ) -> ChatResponse:
        """Process one message through all scope, safety and RAG stages."""

        message = " ".join(message.split()).strip()
        if not message:
            raise ValueError("Message cannot be empty")
        if len(message) > self.settings.websocket_max_message_chars:
            raise ValueError("Message is longer than the configured limit")

        session = get_or_create_session(db, session_id=session_id, title=message[:80])
        self._persist_user_message(db, session.id, message)

        if self.medical_guard.is_greeting(message):
            response = ChatResponse(
                answer=(
                    "Hello! I can help with medical information and approved "
                    "hospital policies. I cannot replace a doctor."
                ),
                category="greeting",
                provider="rules",
                session_id=session.id,
                safety_notice=self.safety_notice,
            )
            self._persist_answer(db, session.id, response)
            return response

        emergency = self.emergency_guard.check(message)
        if emergency.detected:
            response = ChatResponse(
                answer=self.emergency_guard.emergency_message,
                category="emergency",
                provider="safety_rules",
                session_id=session.id,
                safety_notice=self.safety_notice,
            )
            self._persist_answer(db, session.id, response)
            return response

        sources = self.rag_service.retrieve(message)
        strongest_score = max((source.score for source in sources), default=0.0)
        scope = self.medical_guard.classify(message, strongest_score)
        if not scope.allowed:
            response = ChatResponse(
                answer=(
                    "I can respond only to greetings and medical or "
                    "hospital-related questions."
                ),
                category="unsupported",
                provider="scope_rules",
                session_id=session.id,
            )
            self._persist_answer(db, session.id, response)
            return response

        if not sources:
            response = ChatResponse(
                answer=(
                    "This appears to be a medical or hospital-related question, "
                    "but the approved knowledge base does not contain enough "
                    "information for a grounded answer. Please ask a qualified "
                    "medical professional or hospital staff member."
                ),
                category=scope.category,
                provider="retrieval_only",
                session_id=session.id,
                safety_notice=self.safety_notice,
            )
            self._persist_answer(db, session.id, response)
            return response

        prompt = self.prompt_builder.build(message, sources)
        provider = create_llm_provider(self.settings)
        try:
            generated = await provider.generate(
                prompt, [source.content for source in sources]
            )
        except Exception:
            logger.exception(
                "Configured generation provider failed; falling back to retrieval-only"
            )
            generated = await RetrievalOnlyProvider().generate(
                prompt, [source.content for source in sources]
            )

        response = ChatResponse(
            answer=generated.text,
            category=scope.category,
            provider=generated.provider,
            session_id=session.id,
            sources=sources,
            safety_notice=self.safety_notice,
        )
        self._persist_answer(db, session.id, response)
        return response
