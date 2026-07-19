"""Configuration loading for authoring automation scripts."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .paths import RepoPaths, find_repo_root


@dataclass
class LLMConfig:
    provider: str = "openai"  # openai | anthropic | openai_compatible
    model: str = "gpt-4.1"
    base_url: str | None = None
    api_key_env: str = "OPENAI_API_KEY"
    temperature: float = 0.3
    max_tokens: int = 16384
    timeout_seconds: int = 600
    max_retries: int = 3


@dataclass
class BookConfig:
    title: str = "AI Agent Engineering Bootcamp (2026 Edition)"
    total_chapters: int = 94
    default_author: str = "AI Agent Engineering Bootcamp"


@dataclass
class Config:
    llm: LLMConfig = field(default_factory=LLMConfig)
    book: BookConfig = field(default_factory=BookConfig)
    dry_run: bool = False
    verbose: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def api_key(self) -> str | None:
        return os.environ.get(self.llm.api_key_env) or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get(
            "OPENAI_API_KEY"
        )


def _merge_dict(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def load_config(
    config_path: Path | None = None,
    *,
    dry_run: bool | None = None,
    verbose: bool | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> Config:
    """Load config from YAML + environment overrides."""
    root = find_repo_root()
    paths = RepoPaths(root)
    path = config_path or paths.config_file

    raw: dict[str, Any] = {}
    if path.is_file():
        with path.open(encoding="utf-8") as fh:
            loaded = yaml.safe_load(fh) or {}
            if not isinstance(loaded, dict):
                raise ValueError(f"Config file must be a mapping: {path}")
            raw = loaded

    # Environment overlays
    env_overlay: dict[str, Any] = {"llm": {}}
    if os.environ.get("BOOK_LLM_PROVIDER"):
        env_overlay["llm"]["provider"] = os.environ["BOOK_LLM_PROVIDER"]
    if os.environ.get("BOOK_LLM_MODEL"):
        env_overlay["llm"]["model"] = os.environ["BOOK_LLM_MODEL"]
    if os.environ.get("BOOK_LLM_BASE_URL"):
        env_overlay["llm"]["base_url"] = os.environ["BOOK_LLM_BASE_URL"]
    if os.environ.get("BOOK_LLM_API_KEY_ENV"):
        env_overlay["llm"]["api_key_env"] = os.environ["BOOK_LLM_API_KEY_ENV"]
    if os.environ.get("BOOK_LLM_TEMPERATURE"):
        env_overlay["llm"]["temperature"] = float(os.environ["BOOK_LLM_TEMPERATURE"])
    if os.environ.get("BOOK_LLM_MAX_TOKENS"):
        env_overlay["llm"]["max_tokens"] = int(os.environ["BOOK_LLM_MAX_TOKENS"])
    raw = _merge_dict(raw, env_overlay)

    llm_raw = raw.get("llm") or {}
    book_raw = raw.get("book") or {}

    cfg = Config(
        llm=LLMConfig(
            provider=str(llm_raw.get("provider", "openai")),
            model=str(llm_raw.get("model", "gpt-4.1")),
            base_url=llm_raw.get("base_url"),
            api_key_env=str(llm_raw.get("api_key_env", "OPENAI_API_KEY")),
            temperature=float(llm_raw.get("temperature", 0.3)),
            max_tokens=int(llm_raw.get("max_tokens", 16384)),
            timeout_seconds=int(llm_raw.get("timeout_seconds", 600)),
            max_retries=int(llm_raw.get("max_retries", 3)),
        ),
        book=BookConfig(
            title=str(book_raw.get("title", "AI Agent Engineering Bootcamp (2026 Edition)")),
            total_chapters=int(book_raw.get("total_chapters", 94)),
            default_author=str(book_raw.get("default_author", "AI Agent Engineering Bootcamp")),
        ),
        dry_run=bool(raw.get("dry_run", False)),
        verbose=bool(raw.get("verbose", False)),
        extra={k: v for k, v in raw.items() if k not in {"llm", "book", "dry_run", "verbose"}},
    )

    if dry_run is not None:
        cfg.dry_run = dry_run
    if verbose is not None:
        cfg.verbose = verbose
    if provider:
        cfg.llm.provider = provider
    if model:
        cfg.llm.model = model

    return cfg
