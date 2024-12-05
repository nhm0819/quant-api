from pydantic import BaseModel, Field
from typing import List, Dict, Tuple, Optional, Literal, Union
import uuid
import datetime


class MarketDataCreate(BaseModel):
    symbols: List[str] = ["BTCUSDT", "ETHUSDT"]
    market_data_type: str = "trades"
    # start_date: str = "2024-11-29"
    # end_date: str = "2024-12-03"
    date_str: str = Field(
        default_factory=lambda x: (datetime.datetime.today() - datetime.timedelta(days=2)).strftime('%Y-%m-%d'))
    trading_type: str = "spot"
    period: str = "daily"
    interval: Optional[str] = "1m"
    # return_type: str = "df"


class MarketDataForQuant(BaseModel):
    # target data
    start_date: str = Field(
        default_factory=lambda x: (datetime.datetime.today() - datetime.timedelta(days=2)).strftime('%Y-%m-%d'))
    end_date: str = Field(
        default_factory=lambda x: (datetime.datetime.today() - datetime.timedelta(days=2)).strftime('%Y-%m-%d'))
    trading_type: str = "spot"
    period: str = "daily"
    interval: Optional[str] = "1m"