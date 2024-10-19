from fastapi import APIRouter, WebSocket
from auth import get_current_token, SECRET_KEY, ALGORITHM

router = APIRouter()

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket, access_token: str):
    resource_uuid = await get_current_token(access_token)
    await websocket.accept()
    await websocket.send_text(f"UUID was: {resource_uuid}")
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
