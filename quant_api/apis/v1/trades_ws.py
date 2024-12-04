from fastapi import FastAPI, APIRouter, WebSocket, HTTPException, WebSocketDisconnect
from fastapi.testclient import TestClient
from quant_api.assemble.websocket import proxy_websocket
from quant_api.configs import settings
import websockets
import asyncio


router = APIRouter(prefix="/trades/ws", tags=["Trade WS"])


@router.websocket("/{symbol}@trade")
async def ws_trade(client_ws: WebSocket, symbol: str):
    await client_ws.accept()
    server_uri = f"wss://{settings.BINANCE_WS_HOST}/ws/{symbol.lower()}@trade"
    await proxy_websocket(client_ws, server_uri)


async def unit_test(client, symbol: str):

    # binance trade ws test
    server_uri = f"wss://{settings.BINANCE_WS_HOST}/ws/{symbol.lower()}@trade"
    try:
        async with websockets.connect(server_uri) as binance_ws:
            data = await binance_ws.recv()
            print(data)
    except WebSocketDisconnect as e:
        print(f"WebSocket connection closed: {e}")

    # fastapi ws test
    uri = f"/trades/ws/{symbol}@trade"
    try:
        with client.websocket_connect(uri) as binance_ws:
            data = binance_ws.receive_json()
            print(data)
    except WebSocketDisconnect as e:
        print(f"WebSocket connection closed: {e}")
    finally:
        print("WebSocket disconnected")


if __name__ == "__main__":
    from quant_api.assemble.middleware import cors_middleware

    app = FastAPI(
        middleware=[
            cors_middleware,
        ],
    )
    app.include_router(router)
    client = TestClient(app)
    symbol = "BTCUSDT"
    result = asyncio.run(unit_test(client=client, symbol=symbol))
