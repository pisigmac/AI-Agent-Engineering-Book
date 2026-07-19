"""Prompt specification and render result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FewShotExample:
    user: str
    assistant: str


@dataclass(frozen=True)
class PromptSpec:
    id: str
    version: str
    description: str = ""
    system: str = ""
    developer: str = ""
    user_template: str = ""
    constraints: tuple[str, ...] = ()
    examples: tuple[FewShotExample, ...] = ()
    required_vars: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    risk: str = "normal"  # normal | high
    max_tokens_est: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.version:
            raise ValueError("id and version are required")
        if not self.system.strip() and not self.user_template.strip():
            raise ValueError("prompt must define system and/or user_template")


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True)
class RenderedPrompt:
    prompt_id: str
    version: str
    messages: tuple[ChatMessage, ...]
    variables: dict[str, str]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_messages(self) -> list[dict[str, str]]:
        return [m.to_dict() for m in self.messages]

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_id": self.prompt_id,
            "version": self.version,
            "variables": dict(self.variables),
            "messages": self.to_messages(),
            "metadata": dict(self.metadata),
        }
