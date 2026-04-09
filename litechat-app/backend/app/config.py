from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llama_server_url: str = "http://127.0.0.1:8080"
    anthropic_api_key: str = ""

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_lite: str = ""
    stripe_price_plus: str = ""

    discord_webhook_url: str = ""

    app_url: str = "https://pik-tal.com"
    database_url: str = "sqlite:///./litechat.db"

    free_messages_per_day: int = 10
    max_context_messages: int = 10
    max_tokens_per_response: int = 1024

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
