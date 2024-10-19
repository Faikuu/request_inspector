from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from auth import get_current_token, SECRET_KEY, ALGORITHM
from connection_manager import ConnectionManager

router = APIRouter()
manager = ConnectionManager()

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket, access_token: str):
    resource_uuid = await get_current_token(access_token)
    if resource_uuid is None:
        await websocket.close(code=1008)
        return
    
    await manager.connect(resource_uuid, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_text(resource_uuid, f"Message from client: {data}")
    except WebSocketDisconnect:
        await manager.disconnect(resource_uuid)

# @router.websocket("/")
# async def websocket_endpoint(websocket: WebSocket, access_token: str):
#     resource_uuid = await get_current_token(access_token)
#     await websocket.accept()
#     await websocket.send_text(f"UUID was: {resource_uuid}")
#     while True:
#         data = await websocket.receive_text()
#         await websocket.send_text(f"Message text was: {data}")