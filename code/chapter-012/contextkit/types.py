"""Domain types for context assembly."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Trust(str, Enum):
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class Kind(str, Enum):
    SYSTEM = "system"
    GOAL = "goal"
    HISTORY = "history"
    TOOL = "tool"
    MEMORY = "memory"


_PRIORITY_RANK = {
    Priority.CRITICAL: 0,
    Priority.HIGH: 1,
    Priority.NORMAL: 2,
    Priority.LOW: 3,
}


def priority_rank(priority: Priority) -> int:
    return _PRIORITY_RANK[priority]


@dataclass
class ContextItem:
    item_id: str
    kind: Kind
    role: str
    content: str
    trust: Trust
    priority: Priority
    created_index: int
    metadata: dict[str, Any] = field(default_factory=dict)
    token_est: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, Kind):
            self.kind = Kind(self.kind)
        if not isinstance(self.trust, Trust):
            self.trust = Trust(self.trust)
        if not isinstance(self.priority, Priority):
            self.priority = Priority(self.priority)
        if not self.item_id:
            raise ValueError("item_id is required")
        if not isinstance(self.content, str):
            raise TypeError("content must be str")


@dataclass
class HistoryTurn:
    role: str
    content: str
    turn_id: str | None = None
    priority: Priority = Priority.NORMAL


@dataclass
class ToolResult:
    call_id: str
    name: str
    content: str
    priority: Priority = Priority.NORMAL


@dataclass
class MemoryHit:
    memory_id: str
    content: str
    score: float = 0.0
    source: str = ""
    priority: Priority = Priority.HIGH


@dataclass
class ContextState:
    """Snapshot of everything that *might* enter the next model call."""

    system_policy: str
    goal: str = ""
    history: list[HistoryTurn] = field(default_factory=list)
    tools: list[ToolResult] = field(default_factory=list)
    memories: list[MemoryHit] = field(default_factory=list)
    policy_id: str | None = None

    def __post_init__(self) -> None:
        if not self.system_policy.strip():
            raise ValueError("system_policy must be non-empty")


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class AssemblyReport:
    budget: int
    tokens_est: int
    kept_ids: list[str]
    dropped_ids: list[str]
    compressed_ids: list[str]
    notes: list[str]
    policy_id: str | None = None

    @property
    def over_budget(self) -> bool:
        return self.tokens_est > self.budget

    def to_dict(self) -> dict[str, Any]:
        return {
            "budget": self.budget,
            "tokens_est": self.tokens_est,
            "over_budget": self.over_budget,
            "kept_ids": list(self.kept_ids),
            "dropped_ids": list(self.dropped_ids),
            "compressed_ids": list(self.compressed_ids),
            "notes": list(self.notes),
            "policy_id": self.policy_id,
        }


@dataclass
class AssemblyResult:
    messages: list[ChatMessage]
    report: AssemblyReport
    items_kept: list[ContextItem]
    items_dropped: list[ContextItem]

    def to_dict(self) -> dict[str, Any]:
        return {
            "messages": [m.to_dict() for m in self.messages],
            "report": self.report.to_dict(),
            "kept": [_item_dict(i) for i in self.items_kept],
            "dropped": [_item_dict(i) for i in self.items_dropped],
        }


def _item_dict(item: ContextItem) -> dict[str, Any]:
    return {
        "item_id": item.item_id,
        "kind": item.kind.value,
        "role": item.role,
        "trust": item.trust.value,
        "priority": item.priority.value,
        "created_index": item.created_index,
        "token_est": item.token_est,
        "metadata": dict(item.metadata),
        "content_preview": item.content[:160],
    }
