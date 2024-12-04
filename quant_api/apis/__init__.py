from quant_api.apis import v1
__all__ = ["v1"]

from fastapi import APIRouter, WebSocket
from fastapi.responses import JSONResponse
from fastapi import HTTPException, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import asyncio
from quant_api.static.ws_test_html import html


router = APIRouter()

@router.get("/", response_class=JSONResponse)
async def index():
    """Index Page of the API."""
    return {"status": "healthy"}


@router.get("/chat", response_class=JSONResponse)
async def chat():
    """chat Page of the API."""
    return HTMLResponse(html)


@router.websocket("/ws")
async def websocket_index(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")


@router.websocket("/ws_ping")
async def websocket_index(websocket: WebSocket):
    await websocket.accept()
    try:
        cnt = 0
        while cnt < 3:
            await websocket.send_json(
                {
                    "status": "healthy"
                }
            )
            cnt += 1
            await asyncio.sleep(1)
        await websocket.send_json({"status": "closed"})
    except WebSocketDisconnect as e:
        print(f"WebSocket connection closed: {e}")
    finally:
        print("WebSocket disconnected")
        await websocket.close()
