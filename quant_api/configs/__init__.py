from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    env: str = "dev"

    rdb_username: str = "crowdworks"
    rdb_password: str = "crowdworks"
    rdb_hostname: str = "crowdworks.ap-northeast-2.rds.amazonaws.com"
    rdb_db_name: str = "CrowdWorks"

    SQLALCHEMY_DATABASE_URL: str = "sqlite+aiosqlite:////tmp/sqlite3.db"

    BINANCE_API_HOST: str = "api.binance.com"
    BINANCE_WS_HOST: str = "stream.binance.com:9443" # "ws-api.binance.com:443/ws-api/v3" # "fstream.binance.com" #  #


settings = Settings()
