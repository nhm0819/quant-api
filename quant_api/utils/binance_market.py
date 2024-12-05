import datetime
import directories
import httpx
from io import BytesIO
from zipfile import ZipFile
import pandas as pd
import asyncio
from typing import Dict, Union, Optional
from quant_api.configs import settings
import logging

logger = logging.getLogger("uvicorn")


def extract_zip_content(
    zip_content, return_type="df"
) -> Dict[str, Union[pd.DataFrame, str, bytes]]:
    with ZipFile(BytesIO(zip_content)) as zf:
        if return_type == "df":
            result = {
                file_name: pd.read_csv(zf.open(file_name), header=None)
                for file_name in zf.namelist()
            }
        else:
            result = {file_name: zf.read(file_name) for file_name in zf.namelist()}
        return result


class BinanceMarket:

    @staticmethod
    def _get_path(
        market_data_type: str,
        date_str: str,
        trading_type: str,
        period: str,
        symbol: str,
        interval: str | None = None,
    ) -> str:
        """
        trading_type : 'um', 'cm', 'spot'
        """
        if trading_type == "spot":
            base_path = (
                f"data/{trading_type}/{period}/{market_data_type}/{symbol.upper()}"
            )
        else:
            base_path = f"data/futures/{trading_type}/{period}/{market_data_type}/{symbol.upper()}"

        if interval and market_data_type != "trades":
            url = f"{settings.BINANCE_MARKET_URL}/{base_path}/{interval}/{symbol.upper()}-{interval}-{date_str}.zip"
        else:
            url = f"{settings.BINANCE_MARKET_URL}/{base_path}/{symbol.upper()}-{market_data_type}-{date_str}.zip"

        assert (
            datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            <= (datetime.datetime.now() - datetime.timedelta(days=1)).date()
        ), Exception(f"cannot get {date_str} data")

        return url

    @classmethod
    def get_data(
        self,
        market_data_type: str,
        date_str: str,
        trading_type: str,
        period: str,
        symbol: str,
        interval: Optional[str] = None,
        return_type: str = "df",
    ) -> Dict[str, Union[pd.DataFrame, str, bytes]]:

        url = self._get_path(
            market_data_type,
            date_str,
            trading_type,
            period,
            symbol,
            interval=interval,
        )

        with httpx.Client() as client:
            try:
                response = client.get(url)
            except:
                raise Exception(f"cannot find url : {url}")
            result = extract_zip_content(response.content, return_type)

        return result

    @classmethod
    async def aget_data(
        self,
        market_data_type: str,
        date_str: str,
        trading_type: str,
        period: str,
        symbol: str,
        interval: Optional[str] = None,
        return_type: str = "df",
    ) -> Dict[str, Union[bytes, pd.DataFrame]]:
        url = self._get_path(
            market_data_type,
            date_str,
            trading_type,
            period,
            symbol,
            interval=interval,
        )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
            except:
                raise Exception(f"cannot find url : {url}")
            result = await asyncio.to_thread(
                extract_zip_content, response.content, return_type
            )

        return result


async def main(
    market_data_type, date_str, trading_type, period, symbol, interval, return_type="df"
):
    # if start_date == end_date:
    #     dates = [start_date]
    # else:
    #     start_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    #     end_dt = min(datetime.datetime.strptime(end_date, '%Y-%m-%d'),
    #                  datetime.datetime.now() - datetime.timedelta(days=2))
    #     dates = [(start_dt + datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in
    #              range((end_dt - start_dt).days + 1)]

    tasks = [
        BinanceMarket.aget_data(
            market_data_type,
            date_str,
            trading_type,
            period,
            symbol,
            interval,
            return_type,
        )
    ]
    result = await asyncio.gather(*tasks)

    # print(result)
    return result


if __name__ == "__main__":

    date_str = "2024-12-02"
    # start_date = '2024-11-28'
    # end_date = '2024-12-02'
    # if start_date == end_date:
    #     dates = [start_date]
    # else:
    #     start_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    #     end_dt = min(datetime.datetime.strptime(end_date, '%Y-%m-%d'),
    #                  datetime.datetime.now() - datetime.timedelta(days=2))
    #     dates = [(start_dt + datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in
    #              range((end_dt - start_dt).days + 1)]

    interval = ""  # "1m"
    # interval =
    symbol = "BTCUSDT"
    trading_type = "spot"
    period = "daily"
    market_data_type = "trades"  # "klines"

    # async
    a_result = asyncio.run(
        main(
            market_data_type,
            date_str,
            trading_type,
            period,
            symbol,
            interval,
            return_type="df",
        )
    )

    # sync
    result = []
    result.append(
        BinanceMarket.get_data(
            market_data_type,
            date_str,
            trading_type,
            period,
            symbol,
            interval,
            return_type="df",
        )
    )

    print(len(result))
