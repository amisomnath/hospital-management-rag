"""Chat persistence helpers."""

from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession


def get_or_create_session(
    db: Session, session_id: str | None = None, title: str | None = None
) -> ChatSession:
    """Return an existing session or create a new conversation."""

    if session_id:
        session = db.get(ChatSession, session_id)
        if session:
            return session

    session = ChatSession(title=title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def add_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    provider: str | None = None,
    sources: list[dict] | None = None,
) -> ChatMessage:
    """Store one user or assistant chat message."""

    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        provider=provider,
        sources=sources,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
