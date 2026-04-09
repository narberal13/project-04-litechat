"""きくよ — 設定。"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_mainichi: str = ""

    discord_webhook_url: str = ""

    app_url: str = "https://pik-tal.com"
    database_url: str = "sqlite:///./kikuyo.db"

    # レート制限
    free_messages_per_day: int = 3
    paid_messages_per_week: int = 70

    # Haiku設定
    max_context_messages: int = 10
    max_tokens_per_response: int = 1024
    haiku_model: str = "claude-haiku-4-5-20251001"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
