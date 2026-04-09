from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Claude API
    anthropic_api_key: str = ""

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_single: str = ""
    stripe_price_monthly: str = ""

    # Resend
    resend_api_key: str = ""
    from_email: str = "noreply@yourdomain.com"

    # Discord
    discord_webhook_url: str = ""

    # App
    app_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"
    database_url: str = "sqlite:///./sitescan.db"

    # Rate limits
    max_free_scans_per_month: int = 3
    max_concurrent_scans: int = 2
    api_monthly_budget_usd: float = 50.0

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
