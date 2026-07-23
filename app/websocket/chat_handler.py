"""Real-time medical chatbot WebSocket loop."""

import logging

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.db.session import SessionLocal
from app.schemas.chat import WebSocketClientMessage
from app.services.chat_service import ChatService
from app.websocket.manager import manager

logger = logging.getLogger(__name__)


async def handle_chat_websocket(
    websocket: WebSocket, session_id: str, user_id: str
) -> None:
    """Receive chat messages and return progress plus final answer events."""

    await manager.connect(session_id, websocket)
    await manager.send_event(
        websocket,
        "connection",
        status="connected",
        session_id=session_id,
        user_id=user_id,
    )

    db = SessionLocal()
    service = ChatService()
    try:
        while True:
            raw = await websocket.receive_json()
            try:
                message = WebSocketClientMessage.model_validate(raw)
            except ValidationError as exc:
                await manager.send_event(
                    websocket,
                    "error",
                    code="INVALID_MESSAGE",
                    message=(
                        "Send JSON with type='chat_message' and a non-empty message."
                    ),
                    details=exc.errors(include_url=False),
                )
                continue

            await manager.send_event(
                websocket,
                "status",
                stage="validating",
                message="Checking medical scope and safety.",
            )
            await manager.send_event(
                websocket,
                "status",
                stage="retrieving",
                message="Searching the approved hospital knowledge base.",
            )

            try:
                response = await service.process(
                    db=db, message=message.message, session_id=session_id
                )
            except ValueError as exc:
                await manager.send_event(
                    websocket,
                    "error",
                    code="INVALID_INPUT",
                    message=str(exc),
                )
                continue
            except Exception:
                logger.exception("WebSocket chat processing failed")
                db.rollback()
                await manager.send_event(
                    websocket,
                    "error",
                    code="CHAT_PROCESSING_FAILED",
                    message="The message could not be processed.",
                )
                continue

            event_type = "rejected" if response.category == "unsupported" else "answer"
            await manager.send_event(
                websocket, event_type, **response.model_dump(mode="json")
            )
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: session=%s", session_id)
    finally:
        manager.disconnect(session_id, websocket)
        db.close()
