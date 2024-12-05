from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    env: str = "dev"

    rdb_username: str = ""
    rdb_password: str = ""
    rdb_hostname: str = ""
    rdb_db_name: str = ""

    SQLALCHEMY_DATABASE_URL: str = "sqlite+aiosqlite:////tmp/sqlite3.db"

    BINANCE_API_URL: str = "https://api.binance.com"
    BINANCE_WS_URL: str = (
        "wss://stream.binance.com:9443"  # "ws-api.binance.com:443/ws-api/v3" # "fstream.binance.com" #  #
    )
    BINANCE_MARKET_URL: str = 'https://data.binance.vision'

    INTERVALS: list = ["1s", "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w",
                       "1mo"]
    DAILY_INTERVALS: list = ["1s", "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d"]
    TRADING_TYPE: list = ["spot", "um", "cm"]

    KLINES_COLUMNS: list = [
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
        "unused"
    ]
    TRADES_COLUMNS: list = [
        'id',
        'price',
        'quantity',
        'quoteQty',
        'time',
        'isBuyerMaker',
        'isBestMatch',
        # 'side'
    ]


settings = Settings()
