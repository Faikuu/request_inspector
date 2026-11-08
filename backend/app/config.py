"""Settings read from RI_* environment variables and backend/.env."""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
MIN_SECRET_KEY_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RI_",
        env_file=BACKEND_DIR / ".env",
        extra="ignore",
    )

    # Signs viewer tokens. Unset: a random key is generated at startup (tokens reset on restart).
    secret_key: str | None = None
    database_url: str = "sqlite+aiosqlite:///./request_inspector.db"
    # Comma-separated browser origins allowed to open the live stream and call the API with CORS.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    token_ttl_minutes: int = Field(default=60, ge=1, le=7 * 24 * 60)
    max_body_bytes: int = Field(default=1_048_576, ge=1)
    max_requests_per_inbox: int = Field(default=500, ge=1)
    session_attempts_per_minute: int = Field(default=10, ge=1)
    inbox_session_attempts_per_minute: int = Field(default=30, ge=1)
    inbox_creates_per_hour: int = Field(default=30, ge=1)
    hook_requests_per_minute: int = Field(default=300, ge=1)
    # Only when a trusted reverse proxy sets X-Forwarded-For. Otherwise the socket address is used.
    trust_proxy_headers: bool = False
    sql_echo: bool = False
    # Serve /docs, /redoc and /openapi.json. Off by default.
    enable_docs: bool = False

    @field_validator("secret_key")
    @classmethod
    def _check_secret_key(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if len(value) < MIN_SECRET_KEY_LENGTH:
            raise ValueError(f"RI_SECRET_KEY must be at least {MIN_SECRET_KEY_LENGTH} characters")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()]
