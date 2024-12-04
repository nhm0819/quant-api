import websockets
from websockets.exceptions import ConnectionClosed
from fastapi.websockets import WebSocket, WebSocketDisconnect
import asyncio

async def proxy_websocket(client_ws: WebSocket, server_uri: str):
    """
    클라이언트 WebSocket과 외부 WebSocket 서버를 연결하고 데이터를 중계합니다.
    """
    try:
        # 외부 WebSocket 서버와 연결
        async with websockets.connect(server_uri) as server_ws:
            # 클라이언트와 서버 간 양방향 데이터 중계
            async def forward_client_to_server():
                try:
                    while True:
                        # 클라이언트로부터 메시지 수신
                        data = await client_ws.receive_text()
                        # 외부 서버로 메시지 전달
                        await server_ws.send(data)
                except WebSocketDisconnect:
                    print("Client disconnected")
                    await server_ws.close()

            async def forward_server_to_client():
                try:
                    while True:
                        # 외부 서버로부터 메시지 수신
                        data = await server_ws.recv()
                        # 클라이언트로 메시지 전달
                        await client_ws.send_text(data)
                except websockets.ConnectionClosed:
                    print("External server disconnected")
                    await client_ws.close()

            # 양방향 데이터 전달을 동시 실행
            await asyncio.gather(forward_client_to_server(), forward_server_to_client())
    except Exception as e:
        print(f"Error occurred: {e}")
        await client_ws.close()