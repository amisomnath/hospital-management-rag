"""Chat and WebSocket schemas."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Question submitted through the HTTP chat endpoint."""

    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None


class SourceReference(BaseModel):
    """One retrieved source shown with an answer."""

    document_id: str | None = None
    document: str
    chunk_id: str | None = None
    section: str | None = None
    page_number: int | None = None
    score: float
    content: str


class ChatResponse(BaseModel):
    """Final chatbot response."""

    answer: str
    category: str
    provider: str
    session_id: str | None = None
    sources: list[SourceReference] = Field(default_factory=list)
    safety_notice: str | None = None


class WebSocketClientMessage(BaseModel):
    """Expected JSON message sent by a WebSocket client."""

    type: Literal["chat_message"] = "chat_message"
    message: str = Field(min_length=1, max_length=4000)


class WebSocketServerMessage(BaseModel):
    """Generic typed WebSocket server event."""

    type: str
    payload: dict[str, Any] = Field(default_factory=dict)
