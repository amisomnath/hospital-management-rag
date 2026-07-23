"""HTTP and WebSocket chatbot endpoints."""

from fastapi import APIRouter, WebSocket

from app.api.deps import CurrentUser, DatabaseSession
from app.core.security import decode_access_token
from app.crud.user import get_user
from app.db.session import SessionLocal
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.websocket.chat_handler import handle_chat_websocket

router = APIRouter(prefix="/chat", tags=["Medical Chatbot"])


@router.post("/query", response_model=ChatResponse)
async def query_chatbot(
    payload: ChatRequest, db: DatabaseSession, _: CurrentUser
) -> ChatResponse:
    """Ask the chatbot through a normal HTTP request."""

    return await ChatService().process(
        db=db, message=payload.message, session_id=payload.session_id
    )


@router.websocket("/ws/{session_id}")
async def chatbot_websocket(websocket: WebSocket, session_id: str) -> None:
    """Handle one real-time medical-chat conversation."""
    token = websocket.query_params.get("token", "")
    with SessionLocal() as db:
        try:
            payload = decode_access_token(token)
            user = get_user(db, str(payload["sub"]))
        except (ValueError, KeyError):
            user = None
        if user is None or not user.is_active:
            await websocket.close(code=1008, reason="Authentication required")
            return
    await handle_chat_websocket(websocket, session_id, user.id)
