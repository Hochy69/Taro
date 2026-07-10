from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str
    telegram_webapp_url: str = "http://localhost:5173"
    telegram_required_channel: str = "best1taro"
    telegram_channel_subscribe_required: bool = False
    api_url: str = "http://localhost:8000"
    internal_api_secret: str = "change-me-internal-secret"
    price_single_spread: int = 59
    price_subscription_1m: int = 399
    price_subscription_3m: int = 999
    price_subscription_6m: int = 1799
    price_compatibility: int = 79
    price_spread_pack_3: int = 149
    price_spread_pack_5: int = 229


settings = Settings()
