"""Finite state machine for agent control flow with guards."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

Guard = Callable[[dict[str, Any]], bool]

@dataclass
class Transition:
    event: str
    target: str
    guard: Guard | None = None

@dataclass
class StateMachine:
    name: str
    initial: str
    transitions: dict[str, list[Transition]] = field(default_factory=dict)
    state: str = ""
    history: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.state = self.initial

    def on(self, state: str, event: str, target: str, guard: Guard | None = None) -> None:
        self.transitions.setdefault(state, []).append(Transition(event, target, guard))

    def send(self, event: str, ctx: dict[str, Any] | None = None) -> str:
        ctx = ctx or {}
        for tr in self.transitions.get(self.state, []):
            if tr.event != event:
                continue
            if tr.guard and not tr.guard(ctx):
                self.history.append({"from": self.state, "event": event, "blocked": True})
                continue
            prev = self.state
            self.state = tr.target
            self.history.append({"from": prev, "event": event, "to": self.state})
            return self.state
        self.history.append({"from": self.state, "event": event, "error": "no_transition"})
        return self.state

def support_fsm() -> StateMachine:
    sm = StateMachine("support", "idle")
    sm.on("idle", "start", "triage")
    sm.on("triage", "needs_tools", "acting")
    sm.on("triage", "simple", "answering")
    sm.on("acting", "tools_done", "answering")
    sm.on("acting", "tool_fail", "triage")
    sm.on("answering", "done", "completed")
    sm.on("answering", "escalate", "human", guard=lambda c: c.get("confidence", 1) < 0.5)
    sm.on("human", "resolved", "completed")
    return sm
