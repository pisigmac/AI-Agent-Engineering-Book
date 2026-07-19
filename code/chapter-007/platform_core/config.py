"""Process settings loaded from environment."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "ai-agent-platform"
    environment: str = "dev"
    default_model: str = "demo"
    provider: str = "mock"  # mock | (future providers)

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=os.getenv("APP_NAME", "ai-agent-platform"),
            environment=os.getenv("APP_ENV", "dev"),
            default_model=os.getenv("DEFAULT_MODEL", "demo"),
            provider=os.getenv("LLM_PROVIDER", "mock"),
        )
