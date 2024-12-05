from pydantic import BaseModel, Field
from typing import List, Dict, Tuple, Optional
import uuid
import datetime


class MultiAssetCryptoStrategy(BaseModel):
    symbols: List[str] = ["BTCUSDT", "ETHUSDT"]
    leverage: float = 1.0
    lookback_periods: Dict[str, int] = {
        "volume": 24,  # Hours for volume profile
        "volatility": 48,  # Hours for volatility calculation
        "correlation": 168,  # Hours for correlation calculation
        "momentum": 12,  # Hours for momentum signals
    }
    position_limits: Optional[Dict[str, float]] = Field(default=None)
    vol_window: int = 24
    vol_threshold: float = 2.0
    min_trade_volume: float = 1000000  # Minimum USD volume
    max_correlation: float = 0.7
    rsi_period: int = 14
    rsi_thresholds: Tuple[float, float] = (30, 70)
