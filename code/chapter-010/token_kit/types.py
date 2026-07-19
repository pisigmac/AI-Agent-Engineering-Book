"""Shared types for token budgeting and context packing."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Priority(str, Enum):
    """Higher priority is retained longer under pressure."""

    CRITICAL = "critical"  # system policy
    HIGH = "high"  # tool definitions, active task
    NORMAL = "normal"  # recent chat
    LOW = "low"  # old chatter, bulky tool dumps already capped


@dataclass(frozen=True)
class ChatMessage:
    role: Role
    content: str
    name: str | None = None
    message_id: str | None = None
    priority: Priority | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.role, Role):
            object.__setattr__(self, "role", Role(self.role))
        if self.priority is not None and not isinstance(self.priority, Priority):
            object.__setattr__(self, "priority", Priority(self.priority))
        if not self.content and self.role is not Role.ASSISTANT:
            # allow empty assistant only as edge case; still require str
            pass
        if not isinstance(self.content, str):
            raise TypeError("content must be str")

    def default_priority(self) -> Priority:
        if self.priority is not None:
            return self.priority
        if self.role is Role.SYSTEM:
            return Priority.CRITICAL
        if self.role is Role.TOOL:
            return Priority.NORMAL
        return Priority.NORMAL


@dataclass(frozen=True)
class BudgetConfig:
    context_window: int
    max_completion: int = 1024
    margin: int = 256
    reserved_system: int = 0
    reserved_tools: int = 0

    def __post_init__(self) -> None:
        if self.context_window <= 0:
            raise ValueError("context_window must be positive")
        if self.max_completion < 0 or self.margin < 0:
            raise ValueError("max_completion and margin must be >= 0")
        if self.reserved_system < 0 or self.reserved_tools < 0:
            raise ValueError("reserved_* must be >= 0")


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int
    output_tokens: int = 0
    tokenizer: str = "unknown"

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True)
class PackResult:
    kept: list[ChatMessage]
    dropped: list[ChatMessage]
    tokens_est: int
    budget: int
    over_budget: bool
    notes: list[str] = field(default_factory=list)
    tokenizer: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "tokens_est": self.tokens_est,
            "budget": self.budget,
            "over_budget": self.over_budget,
            "tokenizer": self.tokenizer,
            "kept_count": len(self.kept),
            "dropped_count": len(self.dropped),
            "dropped_ids": [m.message_id for m in self.dropped],
            "notes": list(self.notes),
            "kept": [_message_dict(m) for m in self.kept],
            "dropped": [_message_dict(m) for m in self.dropped],
        }


def _message_dict(m: ChatMessage) -> dict[str, Any]:
    return {
        "role": m.role.value,
        "content": m.content,
        "name": m.name,
        "message_id": m.message_id,
        "priority": (m.priority or m.default_priority()).value,
    }
