"""Minimal chat message types for the concept lab."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.role not in {"system", "user", "assistant", "tool"}:
            raise ValueError(f"invalid role: {self.role}")
        if not self.content.strip():
            raise ValueError("content must not be empty")


@dataclass(frozen=True)
class CompletionResult:
    text: str
    model: str
    mode: str
    grounded: bool
    usage_tokens: int = 0
