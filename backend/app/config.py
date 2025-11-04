"""
Application Configuration Module

Implements 12-factor app methodology with environment-based configuration.
All settings are loaded from environment variables with sensible defaults.
"""

from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with type validation.

    All configuration is loaded from environment variables or .env file.
    See .env.example for all available options.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    env: Literal["development", "production", "local"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    secret_key: str = Field(..., min_length=32, description="Secret key for encryption")
    api_v1_prefix: str = "/api/v1"

    # Database Backend Selection
    db_backend: Literal["postgres", "dynamo"] = "postgres"

    # PostgreSQL (On-Premises)
    database_url: str = Field(
        default="postgresql://opendeck_user:opendeck_pass@localhost:5432/opendeck",
        description="PostgreSQL connection string",
    )

    # DynamoDB (AWS - Phase 3)
    aws_region: str = "us-east-1"
    dynamo_decks_table: str = "opendeck-decks"
    dynamo_cards_table: str = "opendeck-cards"
    dynamo_users_table: str = "opendeck-users"
    dynamo_docs_table: str = "opendeck-documents"

    # JWT Configuration
    jwt_secret_key: str = Field(..., min_length=32, description="JWT signing secret")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    allowed_origins: str = Field(
        default="http://localhost:4200,http://localhost:3000",
        description="Allowed CORS origins (comma-separated)",
    )

    # Rate Limiting
    rate_limit_per_minute: int = 60

    # AI Services
    ai_provider: Literal["openai", "anthropic", "ollama"] = "openai"

    # OpenAI Configuration
    openai_api_key: str | None = None
    openai_model: str = "gpt-4"

    # Anthropic Configuration
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-sonnet-20240229"

    # Ollama Configuration (local models)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"
    ollama_timeout_seconds: int = 300  # 5 minutes for large documents

    # Common AI Settings
    ai_max_retries: int = 3
    ai_timeout_seconds: int = 60

    # Storage Configuration
    storage_backend: Literal["local", "s3"] = "local"
    storage_path: str = "/tmp/opendeck/documents"
    max_file_size_mb: int = 10
    max_total_upload_size_mb: int = 50
    max_files_per_upload: int = 10
    allowed_file_types: str = "pdf,docx,pptx,txt"

    # S3 Configuration (when storage_backend=s3)
    s3_bucket: str | None = None
    s3_region: str = "us-east-1"
    s3_presigned_url_expiration: int = 3600  # 1 hour

    # Background Processing
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    celery_task_soft_time_limit: int = 600  # 10 minutes
    celery_task_time_limit: int = 900  # 15 minutes

    # AWS SQS (alternative to Redis for production)
    sqs_queue_url: str | None = None

    # Firebase Cloud Messaging
    firebase_credentials_path: str | None = None  # Path to Firebase service account JSON file

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: str | list[str]) -> str:
        """Parse comma-separated origins from environment variable."""
        if isinstance(v, list):
            return ",".join(v)
        return v

    @property
    def origins_list(self) -> list[str]:
        """Get allowed origins as a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.env in ("development", "local")

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.env == "production"

    @property
    def allowed_file_types_list(self) -> list[str]:
        """Get allowed file types as a list."""
        return [ft.strip() for ft in self.allowed_file_types.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024

    @property
    def max_total_upload_size_bytes(self) -> int:
        """Get max total upload size in bytes."""
        return self.max_total_upload_size_mb * 1024 * 1024


# Global settings instance
settings = Settings()
