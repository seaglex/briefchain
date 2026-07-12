"""API configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    jwt_secret_key: str = "local-development-secret-key-do-not-use-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    database_url: str = "sqlite:///./briefchain.db"

    # LLM provider configuration for Arbiter review skill.
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    llm_model: str | None = None

    # Arbiter worker configuration.
    worker_poll_interval: float = 2.0
    worker_max_retries: int = 3
    worker_health_check_interval: float = 60.0
    worker_processing_timeout: float = 300.0

    # Queue backend: "database" (default) or "redis" (future).
    queue_backend: str = "database"

    # Default webhook URL for Arbiter review notifications.
    arbiter_webhook_url: str | None = None

    # Bypass LLM review and mark reviews as force_skipped when true.
    skip_review: bool = False

    # Whether to spawn the Arbiter worker subprocess on startup.
    arbiter_worker_spawn: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
