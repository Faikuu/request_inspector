"""Per-inbox WebSocket fan-out."""

import asyncio
import json
from typing import Any

from fastapi import WebSocket

SEND_TIMEOUT_SECONDS = 5.0


class StreamHub:
    def __init__(self) -> None:
        self._sockets: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, inbox_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._sockets.setdefault(inbox_id, set()).add(websocket)

    async def disconnect(self, inbox_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            members = self._sockets.get(inbox_id)
            if members is None:
                return
            members.discard(websocket)
            if not members:
                del self._sockets[inbox_id]

    async def broadcast(self, inbox_id: str, event: dict[str, Any]) -> None:
        """Send `event` to every socket on the inbox. Sockets that fail are dropped, never raised."""
        async with self._lock:
            targets = list(self._sockets.get(inbox_id, ()))
        if not targets:
            return
        payload = json.dumps(event)
        results = await asyncio.gather(*(self._send(ws, payload) for ws in targets))
        for websocket, ok in zip(targets, results):
            if not ok:
                await self.disconnect(inbox_id, websocket)

    async def close_all(self, inbox_id: str, code: int) -> None:
        async with self._lock:
            members = self._sockets.pop(inbox_id, set())
        for websocket in members:
            try:
                await asyncio.wait_for(websocket.close(code=code), timeout=SEND_TIMEOUT_SECONDS)
            except Exception:  # the client already went away
                pass

    @staticmethod
    async def _send(websocket: WebSocket, payload: str) -> bool:
        try:
            await asyncio.wait_for(websocket.send_text(payload), timeout=SEND_TIMEOUT_SECONDS)
            return True
        except Exception:  # closed, broken or too slow
            return False
