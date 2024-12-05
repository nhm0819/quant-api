from fastapi import FastAPI
from fastapi import APIRouter, WebSocket
from fastapi.responses import JSONResponse
from fastapi import HTTPException, WebSocketDisconnect
from quant_api.quant import MultiAssetCryptoStrategy
from quant_api.apis.v1.klines import get_klines
from quant_api.apis.v1.trades import get_trades
import pandas as pd
import json
from quant_api.configs import settings
from quant_api.schemas import quant, market
from quant_api.utils.encoder import EnhancedJSONEncoder
from quant_api.utils.binance_market import BinanceMarket
import datetime
import logging
import asyncio
import time

router = APIRouter(prefix="/quant", tags=["Quant Forward"])
logger = logging.getLogger("uvicorn")


@router.get("/multi_asset_crypto", response_class=JSONResponse)
async def get_multi_asset_result(symbols: list, interval: str = "1m", limit: int = 500):
    klines_data = {}
    trades_data = {}

    init_params = quant.MultiAssetCryptoStrategy(symbols=symbols).model_dump()
    multi_asset_crypto_strategy = MultiAssetCryptoStrategy(**init_params)

    for symbol in symbols:
        kline_df = pd.DataFrame(
            await get_klines(symbol=symbol, interval=interval, limit=limit)
        )
        kline_df.columns = settings.KLINES_COLUMNS
        kline_df = kline_df.astype(
            {
                "open": "float",
                "close": "float",
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

    return json.dumps(result, cls=EnhancedJSONEncoder)



@router.post("/multi_asset_crypto/past", response_class=JSONResponse)
async def multi_asset_crypto_past(
    target: market.MarketDataForQuant,
    quant_params: quant.MultiAssetCryptoStrategy
):

    # calc date range
    if target.start_date == target.end_date:
        dates = [target.start_date]
    else:
        start_dt = datetime.datetime.strptime(target.start_date, '%Y-%m-%d')
        end_dt = min(datetime.datetime.strptime(target.end_date, '%Y-%m-%d'),
                     datetime.datetime.now() - datetime.timedelta(days=2))
        dates = [(start_dt + datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in
                 range((end_dt - start_dt).days + 1)]

    # symbol to upper case
    symbols = [sb.upper() for sb in quant_params.symbols]

    # data dict init
    klines_data = {}
    trades_data = {}

    # get klines data
    logger.debug("getting klines data...")
    for symbol in symbols:
        klines_data[symbol.upper()] = pd.DataFrame(columns=settings.KLINES_COLUMNS)

        # async tasks
        tasks_klines = [
            BinanceMarket.aget_data(
                market_data_type="klines",
                date_str=date_str,
                trading_type=target.trading_type,
                period=target.period,
                symbol=symbol,
                interval=target.interval,
            )
            for date_str in dates
        ]

        klines_market = await asyncio.gather(*tasks_klines)

        # sum data
        for klines in klines_market:
            klines_data[symbol.upper()] = pd.concat([klines_data[symbol.upper()], list(klines.values())[0]])

        klines_data[symbol.upper()] = klines_data[symbol.upper()].astype(
            {
                "open": "float",
                "close": "float",
                "openPrice": "float",
                "high": "float",
                "low": "float",
                "last": "float",
                "volume": "float",
                "quoteVolume": "float",
            }
        )

    # get trades data
    logger.debug("getting trades data...")
    for symbol in symbols:
        trades_data[symbol.upper()] = pd.DataFrame(columns=settings.TRADES_COLUMNS)

        # async tasks
        tasks_trades = [
            BinanceMarket.aget_data(
                market_data_type="trades",
                date_str=date_str,
                trading_type=target.trading_type,
                period=target.period,
                symbol=symbol,
                interval="",
            )
            for date_str in dates
        ]

        # gather tasks
        trades_market = await asyncio.gather(*tasks_trades)

        # sum data
        for trades in trades_market:
            trades_data[symbol.upper()] = pd.concat([trades_data[symbol.upper()], list(trades.values())[0]])

        # df post process
        trades_data[symbol.upper()] = trades_data[symbol.upper()].astype(
            {"price": "float", "quantity": "float", "quoteQty": "float"}
        )
        trades_data[symbol.upper()]["side"] = trades_data[symbol.upper()].apply(
            lambda row: "BUY" if row["isBuyerMaker"] else "SELL", axis=1
        )

    # Quant
    logger.debug("operating quant func...")
    print("Quant...")
    st = time.time()
    multi_asset_crypto_strategy = MultiAssetCryptoStrategy(**quant_params.model_dump())
    result = multi_asset_crypto_strategy.run_iteration(
        klines_data=klines_data, trades_data=trades_data
    )
    print("quant time :", time.time() - st)

    return json.dumps(result, cls=EnhancedJSONEncoder)


async def unit_test(symbols: list, interval: str = "1m", limit: int = 500):
    result = await get_multi_asset_result(symbols, interval, limit=limit)
    print(result)
    return result


if __name__ == "__main__":

    symbols = ["BTCUSDT", "ETHUSDT"]
    interval = "1m"

    res = asyncio.run(unit_test(symbols=symbols, interval=interval, limit=1000))

    print("end")