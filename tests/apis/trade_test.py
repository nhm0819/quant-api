import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from websockets.exceptions import ConnectionClosed
import websockets
from pytest_mock import MockerFixture


# @pytest.mark.asyncio
# async def test_get_trade(async_client: AsyncClient) -> None:
#     symbol = "BTCUSDT"
#     interval = "1m"
#
#     response = await async_client.get(f"/v1/trades/get/{symbol}/{interval}")
#     assert response.status_code == 200
#     # print(response.json)


def test_ws_trade(client: TestClient) -> None:
    symbol = "BTCUSDT"

    with client.websocket_connect(f"/v1/trades/ws/{symbol}@trade") as websocket:
    #     while True:
        try:
            data = websocket.receive_json()
            print(data)
        except ConnectionClosed as e:
            print(f"Connection closed: {e.__str__()}")
            # break  # 연결이 끊어지면 루프를 종료
