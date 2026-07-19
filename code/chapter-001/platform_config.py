"""Process settings for the Chapter 1 platform scaffold."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # optional at bootstrap

    def load_dotenv(*_args, **_kwargs) -> bool:  # type: ignore[misc]
        return False


@dataclass(frozen=True)
class Settings:
    """Process settings loaded from environment variables."""

    app_name: str = "ai-agent-platform"
    environment: str = "dev"
    log_level: str = "INFO"
    openai_api_key: str | None = None

    @classmethod
    def from_env(cls, env_file: str | None = ".env") -> "Settings":
        if env_file and Path(env_file).is_file():
            load_dotenv(env_file)
        return cls(
            app_name=os.getenv("APP_NAME", "ai-agent-platform"),
            environment=os.getenv("APP_ENV", "dev"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )


def require_non_secret_summary(settings: Settings) -> dict[str, str]:
    """Return a log-safe settings summary (never include secret values)."""
    return {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "log_level": settings.log_level,
        "openai_api_key_set": "yes" if settings.openai_api_key else "no",
    }
