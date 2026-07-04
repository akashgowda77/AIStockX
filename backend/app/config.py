import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "..", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    jwt_secret: str = "development-secret-change-before-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    app_name: str = "AIStockX"
    api_version: str = "v1"

    database_url: str = "sqlite:///./ai_stockx.db"

    frontend_origin: str = "http://localhost:5173"

    finnhub_api_key: str = "change_me"
    alpha_vantage_api_key: str = "change_me"


settings = Settings()