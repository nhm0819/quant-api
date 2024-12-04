from fastapi import FastAPI
from fastapi import APIRouter, WebSocket
from fastapi.responses import JSONResponse
from fastapi import HTTPException, WebSocketDisconnect
from quant_api.strategy import MultiAssetCryptoStrategy
from quant_api.apis.v1.klines import get_klines
from quant_api.apis.v1.trades import get_trades
import pandas as pd
import json
from quant_api.configs import settings
from quant_api.schemas import strategy

import asyncio

router = APIRouter(prefix="/strategy", tags=["Strategy"])


@router.get("/multi_asset_crypto", response_class=JSONResponse)
async def get_multi_asset_result(symbols: list, interval: str = "1m", limit: int = 500):
    klines_data = {}
    trades_data = {}

    init_params = strategy.MultiAssetCryptoStrategyCreate(symbols=symbols).model_dump()
    multi_asset_crypto_strategy = MultiAssetCryptoStrategy(**init_params)

    for symbol in symbols:
        kline_df = pd.DataFrame(
            await get_klines(symbol=symbol, interval=interval, limit=limit)
        )
        kline_df.columns = [
            "open",
            "openPrice",
            "high",
            "low",
            "last",
            "volume",
            "close",
            "quoteVolume",
            "count",
            "takerBaseVolume",
            "takerQuoteVolume",
            "unused",
        ]
        kline_df = kline_df.astype(
            {
                "open": "int",
                "close": "int",
                "openPrice": "float32",
                "high": "float32",
                "low": "float32",
                "last": "float32",
                "volume": "float32",
                "quoteVolume": "float32",
            }
        )

        trade_df = pd.DataFrame(await get_trades(symbol=symbol, limit=limit))
        trade_df = trade_df.rename(columns={"qty": "quantity"})
        trade_df = trade_df.astype(
            {"price": "float32", "quantity": "float32", "quoteQty": "float32"}
        )
        trade_df["side"] = trade_df.apply(
            lambda row: "BUY" if row["isBuyerMaker"] else "SELL", axis=1
        )

        klines_data[symbol] = kline_df
        trades_data[symbol] = trade_df

    result = multi_asset_crypto_strategy.run_iteration(
        klines_data=klines_data, trades_data=trades_data
    )
    # print(result)
    return json.dumps(result)


async def unit_test(symbols: list, interval: str = "1m"):
    result = get_multi_asset_result(symbols, interval)
    return result


if __name__ == "__main__":

    symbols = ["BTC-USDT"]
    interval = "1m"

    res = asyncio.run(unit_test(symbols=symbols, interval=interval))

    print("end")
