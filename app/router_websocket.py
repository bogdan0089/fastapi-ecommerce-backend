from fastapi import WebSocket, APIRouter
from utils.connection_manager import connection


router_websocket = APIRouter()


@router_websocket.websocket("/ws/admin")
async def websocket_endpoint(websocket: WebSocket):
    await connection.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        connection.disconnect(websocket)