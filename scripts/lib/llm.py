"""LLM client abstraction for chapter/code generation and review."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Config, LLMConfig

logger = logging.getLogger("book.llm")


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: dict[str, Any]
    raw: Any = None


class LLMError(RuntimeError):
    """Raised when an LLM call fails after retries."""


class LLMClient:
    """Multi-provider chat completion client."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.llm: LLMConfig = config.llm

    def complete(
        self,
        *,
        system: str,
        user: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        if self.config.dry_run:
            preview = (
                f"[DRY-RUN] Would call {self.llm.provider}/{self.llm.model}\n\n"
                f"--- SYSTEM ({len(system)} chars) ---\n{system[:500]}...\n\n"
                f"--- USER ({len(user)} chars) ---\n{user[:1000]}...\n"
            )
            return LLMResponse(
                content=preview,
                model=self.llm.model,
                provider=self.llm.provider,
                usage={"dry_run": True},
            )

        provider = self.llm.provider.lower()
        last_error: Exception | None = None
        attempts = max(1, self.llm.max_retries)

        for attempt in range(1, attempts + 1):
            try:
                if provider in {"openai", "openai_compatible"}:
                    return self._complete_openai(system, user, temperature, max_tokens)
                if provider == "anthropic":
                    return self._complete_anthropic(system, user, temperature, max_tokens)
                raise LLMError(f"Unsupported LLM provider: {self.llm.provider}")
            except Exception as exc:  # noqa: BLE001 — intentional retry boundary
                last_error = exc
                wait = min(2**attempt, 30)
                logger.warning(
                    "LLM attempt %s/%s failed: %s; retrying in %ss",
                    attempt,
                    attempts,
                    exc,
                    wait,
                )
                if attempt < attempts:
                    time.sleep(wait)

        raise LLMError(f"LLM call failed after {attempts} attempts: {last_error}") from last_error

    def _require_api_key(self) -> str:
        key = self.config.api_key
        if not key:
            raise LLMError(
                f"Missing API key. Set {self.llm.api_key_env} (or OPENAI_API_KEY / ANTHROPIC_API_KEY)."
            )
        return key

    def _complete_openai(
        self,
        system: str,
        user: str,
        temperature: float | None,
        max_tokens: int | None,
    ) -> LLMResponse:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMError("openai package is required. pip install openai") from exc

        client_kwargs: dict[str, Any] = {"api_key": self._require_api_key()}
        if self.llm.base_url:
            client_kwargs["base_url"] = self.llm.base_url
        client = OpenAI(**client_kwargs, timeout=self.llm.timeout_seconds)

        response = client.chat.completions.create(
            model=self.llm.model,
            temperature=temperature if temperature is not None else self.llm.temperature,
            max_tokens=max_tokens or self.llm.max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        content = response.choices[0].message.content or ""
        usage = {}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        return LLMResponse(
            content=content,
            model=response.model or self.llm.model,
            provider="openai",
            usage=usage,
            raw=response,
        )

    def _complete_anthropic(
        self,
        system: str,
        user: str,
        temperature: float | None,
        max_tokens: int | None,
    ) -> LLMResponse:
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise LLMError("anthropic package is required. pip install anthropic") from exc

        client = Anthropic(api_key=self._require_api_key(), timeout=self.llm.timeout_seconds)
        response = client.messages.create(
            model=self.llm.model,
            max_tokens=max_tokens or self.llm.max_tokens,
            temperature=temperature if temperature is not None else self.llm.temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        parts = []
        for block in response.content:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        content = "\n".join(parts)
        usage = {
            "input_tokens": getattr(response.usage, "input_tokens", None),
            "output_tokens": getattr(response.usage, "output_tokens", None),
        }
        return LLMResponse(
            content=content,
            model=response.model or self.llm.model,
            provider="anthropic",
            usage=usage,
            raw=response,
        )


def save_prompt_bundle(
    path: Path,
    *,
    system: str,
    user: str,
    meta: dict[str, Any] | None = None,
) -> None:
    """Persist prompt package for audit / dry-run / offline use."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": meta or {},
        "system": system,
        "user": user,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
