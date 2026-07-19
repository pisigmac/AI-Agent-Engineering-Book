"""Domain types shared across ports and services."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CompletionRequest:
    prompt: str
    model: str = "demo"
    temperature: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CompletionResponse:
    text: str
    model: str
    usage_tokens: int = 0


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    goal: str
    output: str
    created_at: float
    provider: str
