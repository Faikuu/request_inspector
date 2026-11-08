"""Live stream. Authentication is the first client message, never a query-string token."""

import asyncio
import json
import time
from urllib.parse import urlsplit

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.config import Settings
from app.models import Inbox
from app.security import decode_viewer_token

router = APIRouter(prefix="/api/inboxes", tags=["stream"])

AUTH_TIMEOUT_SECONDS = 5
CLOSE_UNAUTHORIZED = 4401
CLOSE_FORBIDDEN_ORIGIN = 4403
CLOSE_INBOX_GONE = 4404


def _origin_allowed(websocket: WebSocket, settings: Settings) -> bool:
    origin = websocket.headers.get("origin")
    if origin is None:  # non-browser clients send no Origin
        return True
    if origin in settings.cors_origin_list:
        return True
    host = websocket.headers.get("host", "")
    return bool(host) and urlsplit(origin).netloc == host  # same-origin deployment


async def _close(websocket: WebSocket, code: int) -> None:
    try:
        await websocket.close(code=code)
    except Exception:  # the client already disconnected
        pass


async def _authenticate(websocket: WebSocket, inbox_id: str, settings: Settings) -> dict | None:
    """Read the first message as {"type":"auth","token":...}. Returns the token claims or None (closed)."""
    try:
        message = await asyncio.wait_for(websocket.receive(), timeout=AUTH_TIMEOUT_SECONDS)
    except (TimeoutError, WebSocketDisconnect):
        await _close(websocket, CLOSE_UNAUTHORIZED)
        return None

    token = None
    if message.get("type") == "websocket.receive" and message.get("text"):
        try:
            data = json.loads(message["text"])
        except ValueError:
            data = None
        if isinstance(data, dict) and data.get("type") == "auth" and isinstance(data.get("token"), str):
            token = data["token"]
    if token is None:
        await _close(websocket, CLOSE_UNAUTHORIZED)
        return None

    try:
        claims = decode_viewer_token(settings, token)
    except jwt.PyJWTError:
        await _close(websocket, CLOSE_UNAUTHORIZED)
        return None
    if claims["sub"] != inbox_id:
        await _close(websocket, CLOSE_UNAUTHORIZED)
        return None
    return claims


async def _hold_open(websocket: WebSocket, expires_at: float) -> None:
    """Read and discard client messages until disconnect or token expiry."""
    while True:
        remaining = expires_at - time.time()
        if remaining <= 0:
            await _close(websocket, CLOSE_UNAUTHORIZED)
            return
        try:
            message = await asyncio.wait_for(websocket.receive(), timeout=remaining)
        except TimeoutError:
            await _close(websocket, CLOSE_UNAUTHORIZED)
            return
        if message.get("type") == "websocket.disconnect":
            return


@router.websocket("/{inbox_id}/stream")
async def inbox_stream(websocket: WebSocket, inbox_id: str) -> None:
    settings: Settings = websocket.app.state.settings
    hub = websocket.app.state.hub

    if not _origin_allowed(websocket, settings):
        await _close(websocket, CLOSE_FORBIDDEN_ORIGIN)  # rejects the handshake
        return
    await websocket.accept()

    claims = await _authenticate(websocket, inbox_id, settings)
    if claims is None:
        return

    async with websocket.app.state.session_factory() as db:
        exists = await db.scalar(select(Inbox.id).where(Inbox.id == inbox_id))
    if exists is None:
        await _close(websocket, CLOSE_INBOX_GONE)
        return

    await hub.connect(inbox_id, websocket)
    try:
        await websocket.send_json({"type": "ready"})
        await _hold_open(websocket, float(claims["exp"]))
    finally:
        await hub.disconnect(inbox_id, websocket)
