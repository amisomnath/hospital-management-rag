"""HTTP and WebSocket chatbot endpoints."""

from fastapi import APIRouter, WebSocket

from app.api.deps import DatabaseSession
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.websocket.chat_handler import handle_chat_websocket

router = APIRouter(prefix="/chat", tags=["Medical Chatbot"])


@router.post("/query", response_model=ChatResponse)
async def query_chatbot(payload: ChatRequest, db: DatabaseSession) -> ChatResponse:
    """Ask the chatbot through a normal HTTP request."""

    return await ChatService().process(
        db=db, message=payload.message, session_id=payload.session_id
    )


@router.websocket("/ws/{session_id}")
async def chatbot_websocket(websocket: WebSocket, session_id: str) -> None:
    """Handle one real-time medical-chat conversation."""

    await handle_chat_websocket(websocket, session_id)
