"""Track active WebSocket clients and send typed events."""

from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """In-memory connection registry for a single FastAPI process."""

    def __init__(self) -> None:
        self.active: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        """Accept and register a WebSocket connection."""

        await websocket.accept()
        self.active[session_id].add(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        """Remove a disconnected client."""

        self.active[session_id].discard(websocket)
        if not self.active[session_id]:
            self.active.pop(session_id, None)

    async def send_event(
        self, websocket: WebSocket, event_type: str, **payload: Any
    ) -> None:
        """Send one JSON event to a client."""

        await websocket.send_json({"type": event_type, **payload})


manager = ConnectionManager()
