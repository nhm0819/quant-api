from fastapi import FastAPI
from fastapi import APIRouter, WebSocket
from fastapi.responses import JSONResponse
from fastapi import HTTPException, WebSocketDisconnect
from quant_api.assemble.websocket import proxy_websocket
import httpx
import websockets
import json
from quant_api.configs import settings
from typing import Optional

import asyncio

router = APIRouter(prefix="/trades")


@router.get("/get/{symbol}", response_class=JSONResponse)
async def get_trades(symbol: str, limit: Optional[int] = 500):
    params = {
        "symbol": symbol.replace("-", ""),
        "limit": limit,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=f"{settings.BINANCE_API_URL}/api/v3/trades", params=params
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code, detail="Binance API Error"
            )

    response_json = response.json()
    return response_json


async def unit_test(symbol: str):
    get_trades_result = await get_trades(symbol=symbol)
    print(get_trades_result)
    return get_trades_result


if __name__ == "__main__":
    result = asyncio.run(unit_test(symbol="BTCUSDT"))
