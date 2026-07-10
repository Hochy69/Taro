from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Tarot Mini App"
    app_env: str = "development"
    debug: bool = True
    secret_key: str
    api_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"

    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080

    telegram_bot_token: str = ""
    telegram_bot_username: str = "best1tarolog_bot"
    telegram_webapp_url: str = ""
    telegram_payment_provider_token: str = ""
    telegram_required_channel: str = "best1taro"
    telegram_channel_subscribe_required: bool = False

    ai_provider: str = "openai"
    ai_model: str = "gpt-4o-mini"
    template_only: bool = True
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    admin_jwt_secret: str = ""
    admin_secret_word: str = "TaroVlad"
    first_admin_telegram_id: int | None = None

    @field_validator("first_admin_telegram_id", mode="before")
    @classmethod
    def empty_admin_id_to_none(cls, v: object) -> object:
        if v == "" or v is None:
            return None
        return v

    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    free_daily_spreads: int = 1
    premium_daily_spreads: int = 15
    free_history_limit: int = 5

    # Free tier: N spreads per rolling period; extra spreads are paid.
    free_spreads_per_period: int = 3
    free_spread_period_days: int = 3

    price_single_spread: int = 59
    price_subscription_1m: int = 399
    price_subscription_3m: int = 999
    price_subscription_6m: int = 1799
    price_compatibility: int = 79

    price_spread_pack_3: int = 149
    price_spread_pack_5: int = 229
    first_paid_discount_percent: int = 30
    love_bundle_discount_percent: int = 20
    referral_premium_trial_days: int = 3

    internal_api_secret: str = "change-me-internal-secret"


settings = Settings()
