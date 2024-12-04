from starlette.testclient import TestClient

from quant_api.apps.v1 import app
from fastapi import HTTPException, WebSocketDisconnect
from fastapi.testclient import TestClient
from websockets.exceptions import ConnectionClosed


def test_websocket_ping(client: TestClient) -> None:
    from quant_api.apps.v1 import app

    symbol = "BTCUSDT"
    interval = "1s"

    client = TestClient(app)
    # with pytest.raises(WebSocketDisconnect):
    # with client.websocket_connect(f"/v1/klines/ws/{symbol}@kline_{interval}") as websocket:
    with client.websocket_connect("/ws_ping") as websocket:
        while True:
            try:
                data = websocket.receive_json()
                print(data)
                if data["status"] == "closed":
                    break
            except ConnectionClosed as e:
                print(f"Connection closed: {e.__str__()}")
                break  # 연결이 끊어지면 루프를 종료