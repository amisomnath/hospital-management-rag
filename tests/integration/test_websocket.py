"""Integration tests for real-time chat messages."""

from fastapi.testclient import TestClient


def _read_until_terminal(websocket):
    for _ in range(10):
        data = websocket.receive_json()
        if data["type"] in {"answer", "rejected", "error"}:
            return data
    raise AssertionError("No terminal WebSocket event received")


def _token(auth_headers: dict[str, str]) -> str:
    return auth_headers["Authorization"].removeprefix("Bearer ")


def test_websocket_greeting(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    path = f"/api/v1/chat/ws/test-session?token={_token(auth_headers)}"
    with client.websocket_connect(path) as websocket:
        assert websocket.receive_json()["type"] == "connection"
        websocket.send_json({"type": "chat_message", "message": "Hello"})
        response = _read_until_terminal(websocket)
        assert response["type"] == "answer"
        assert response["category"] == "greeting"


def test_websocket_rejects_non_medical_question(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    path = f"/api/v1/chat/ws/test-session-2?token={_token(auth_headers)}"
    with client.websocket_connect(path) as websocket:
        websocket.receive_json()
        websocket.send_json(
            {"type": "chat_message", "message": "Write a Python function"}
        )
        response = _read_until_terminal(websocket)
        assert response["type"] == "rejected"
        assert response["category"] == "unsupported"
