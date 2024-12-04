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
from quant_api.utils import encoder

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
                "openPrice": "float",
                "high": "float",
                "low": "float",
                "last": "float",
                "volume": "float",
                "quoteVolume": "float",
            }
        )

        trade_df = pd.DataFrame(await get_trades(symbol=symbol, limit=limit))
        trade_df = trade_df.rename(columns={"qty": "quantity"})
        trade_df = trade_df.astype(
            {"price": "float", "quantity": "float", "quoteQty": "float"}
        )
        trade_df["side"] = trade_df.apply(
            lambda row: "BUY" if row["isBuyerMaker"] else "SELL", axis=1
        )

        klines_data[symbol] = kline_df
        trades_data[symbol] = trade_df

    result = multi_asset_crypto_strategy.run_iteration(
        klines_data=klines_data, trades_data=trades_data
    )

    return json.dumps(result, cls=encoder.EnhancedJSONEncoder)


async def unit_test(symbols: list, interval: str = "1m", limit: int = 500):
    result = await get_multi_asset_result(symbols, interval, limit=limit)
    print(result)
    return result


if __name__ == "__main__":

    symbols = ["BTC-USDT", "ETH-USDT"]
    interval = "1m"

    res = asyncio.run(unit_test(symbols=symbols, interval=interval, limit=1000))

    print("end")
