from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str
    telegram_webapp_url: str = "http://localhost:5173"
    api_url: str = "http://localhost:8000"
    internal_api_secret: str = "change-me-internal-secret"
    price_single_spread: int = 69
    price_subscription_1m: int = 450
    price_subscription_3m: int = 1200
    price_subscription_6m: int = 2100
    price_compatibility: int = 99
    price_spread_pack_3: int = 249
    price_spread_pack_5: int = 399


settings = Settings()
