"""Composable multi-agent orchestration platform."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol
import time
import uuid


@dataclass
class AgentMessage:
    id: str
    sender: str
    recipient: str
    content: str
    kind: str = "task"  # task|result|broadcast
    meta: dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)


@dataclass
class MessageBus:
    log: list[AgentMessage] = field(default_factory=list)

    def send(self, msg: AgentMessage) -> None:
        self.log.append(msg)

    def for_recipient(self, name: str) -> list[AgentMessage]:
        return [m for m in self.log if m.recipient == name or m.recipient == "*"]


Handler = Callable[[str, dict[str, Any]], str]


@dataclass
class AgentSpec:
    name: str
    skills: list[str]
    handler: Handler


@dataclass
class Router:
    agents: list[AgentSpec]

    def route(self, task: str) -> AgentSpec:
        t = task.lower()
        best: AgentSpec | None = None
        best_score = -1
        for a in self.agents:
            score = sum(1 for s in a.skills if s.lower() in t)
            if score > best_score:
                best_score = score
                best = a
        if best is None:
            raise RuntimeError("no agents")
        # default first agent if no skill match
        if best_score <= 0:
            return self.agents[0]
        return best


class LLM(Protocol):
    def merge(self, task: str, parts: list[str]) -> str: ...


@dataclass
class MockLLM:
    def merge(self, task: str, parts: list[str]) -> str:
        body = " | ".join(parts)
        return f"Merged for '{task}': {body}"


@dataclass
class MultiAgentPlatform:
    agents: list[AgentSpec]
    llm: LLM
    bus: MessageBus = field(default_factory=MessageBus)
    events: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.router = Router(self.agents)

    def run(self, task: str, *, fanout: bool = False) -> dict[str, Any]:
        run_id = str(uuid.uuid4())[:8]
        self.events.append({"type": "run_start", "run_id": run_id, "task": task})
        if fanout:
            selected = list(self.agents)
        else:
            selected = [self.router.route(task)]
        results: list[str] = []
        for agent in selected:
            msg = AgentMessage(
                id=str(uuid.uuid4())[:8],
                sender="orchestrator",
                recipient=agent.name,
                content=task,
            )
            self.bus.send(msg)
            out = agent.handler(task, {"run_id": run_id})
            self.bus.send(
                AgentMessage(
                    id=str(uuid.uuid4())[:8],
                    sender=agent.name,
                    recipient="orchestrator",
                    content=out,
                    kind="result",
                )
            )
            results.append(f"{agent.name}: {out}")
            self.events.append({"type": "agent_result", "agent": agent.name})
        final = self.llm.merge(task, results) if len(results) > 1 else results[0]
        self.events.append({"type": "run_done", "run_id": run_id})
        return {
            "run_id": run_id,
            "task": task,
            "agents": [a.name for a in selected],
            "result": final,
            "bus_size": len(self.bus.log),
            "events": self.events,
        }
