from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List

class ConnectionManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConnectionManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "active_connections"):
            self.active_connections: List[tuple[str, WebSocket]] = []

    async def connect(self, recipent: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append((recipent, websocket))

    async def disconnect(self, recipent: str):
        for r, connection in self.active_connections:
            if r == recipent:
                self.active_connections.remove((r, connection))
                await connection.close()

    async def send_text(self, recipent: str, message: str):
        for r, connection in self.active_connections:
            if r == recipent:
                await connection.send_text(message)
