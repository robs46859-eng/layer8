from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="enterprise-ai-routing-proxy", alias="APP_NAME")
    environment: str = Field(default="dev", alias="ENVIRONMENT")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    backend_mode: str = Field(default="memory", alias="BACKEND_MODE")
    database_url: str = Field(
        default="postgresql+psycopg://proxy_user:proxy_pass@localhost:5432/ai_proxy",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    s3_bucket: str = Field(default="ai-proxy-audit", alias="S3_BUCKET")
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    aws_access_key_id: str = Field(default="", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="", alias="AWS_SECRET_ACCESS_KEY")
    aws_endpoint_url: str | None = Field(default=None, alias="AWS_ENDPOINT_URL")
    s3_endpoint_url: str | None = Field(default=None, alias="S3_ENDPOINT_URL")
    audit_queue_url: str = Field(default="", alias="AUDIT_QUEUE_URL")
    default_provider: str = Field(default="mock", alias="DEFAULT_PROVIDER")
    enable_prompt_logging: bool = Field(default=False, alias="ENABLE_PROMPT_LOGGING")
    rate_limit_requests_per_minute: int = Field(default=120, alias="RATE_LIMIT_REQUESTS_PER_MINUTE")
    plugin_timeout_ms: int = Field(default=100, alias="PLUGIN_TIMEOUT_MS")
    cache_ttl_seconds: int = Field(default=300, alias="CACHE_TTL_SECONDS")
    cache_s3_threshold_bytes: int = Field(default=4096, alias="CACHE_S3_THRESHOLD_BYTES")
    worker_poll_seconds: int = Field(default=5, alias="WORKER_POLL_SECONDS")
    worker_batch_size: int = Field(default=5, alias="WORKER_BATCH_SIZE")
    startup_checks_enabled: bool = Field(default=True, alias="STARTUP_CHECKS_ENABLED")
    startup_checks_strict: bool = Field(default=False, alias="STARTUP_CHECKS_STRICT")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    admin_api_token: str = Field(default="", alias="ADMIN_API_TOKEN")
    dev_api_key_prefix: str = Field(default="ak_live_demo", alias="DEV_API_KEY_PREFIX")
    dev_api_key_secret: str = Field(default="change-me-now", alias="DEV_API_KEY_SECRET")


@lru_cache
def get_settings() -> Settings:
    return Settings()
