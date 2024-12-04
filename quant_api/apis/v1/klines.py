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

router = APIRouter(prefix="/klines")


@router.get("/get/{symbol}/{interval}", response_class=JSONResponse)
async def get_klines(
    symbol: str,
    interval: str = "1m",
    startTime: Optional[int] = None,
    endTime: Optional[int] = None,
    timeZone: Optional[str] = "0",
    limit: Optional[int] = 500,
):
    params = {
        "symbol": symbol.replace("-", ""),
        "interval": interval,
        "timeZone": timeZone,
        "limit": limit,
    }
    if startTime:
        params["startTime"] = startTime
    if endTime:
        params["endTime"] = startTime

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=f"https://{settings.BINANCE_API_HOST}/api/v3/klines", params=params
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code, detail="Binance API Error"
            )

    response_json = response.json()
    return response_json


async def unit_test(symbol: str, interval: str = "1m"):
    get_klines_result = await get_klines(symbol=symbol, interval=interval)
    print(get_klines_result)
    return get_klines_result


if __name__ == "__main__":
    result = asyncio.run(unit_test(symbol="BTCUSDT", interval="1s"))
