"""Agent identity, goals, and lifecycle states."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class AgentState(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    WAITING = "waiting"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Goal:
    description: str
    success_criteria: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class Observation:
    content: str
    source: str = "env"
    ok: bool = True

@dataclass
class Action:
    kind: str  # "act" | "finish" | "fail"
    name: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    message: str = ""

@dataclass
class AgentResult:
    ok: bool
    state: AgentState
    message: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "state": self.state.value, "message": self.message, "steps": self.steps}
