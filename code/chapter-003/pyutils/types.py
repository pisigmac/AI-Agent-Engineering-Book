"""Shared message types for LLM-style boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from pyutils.errors import ValidationError

_ALLOWED_ROLES = frozenset({"system", "user", "assistant", "tool"})


@dataclass(frozen=True)
class Message:
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.role not in _ALLOWED_ROLES:
            raise ValidationError(f"invalid role: {self.role}")
        if not isinstance(self.content, str):
            raise ValidationError("content must be str")
        if not self.content.strip():
            raise ValidationError("content must not be empty")


class Tokenizer(Protocol):
    def tokenize(self, text: str) -> list[str]: ...


class WhitespaceTokenizer:
    """Naive tokenizer for demos and tests."""

    def tokenize(self, text: str) -> list[str]:
        return [part for part in text.strip().split() if part]
