"""Google ADK-style agent + runner + session events (offline)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator

@dataclass
class Tool:
    name: str
    run: Callable[..., Any]

@dataclass
class LlmAgent:
    name: str
    instruction: str
    tools: list[Tool] = field(default_factory=list)
    def step(self, message: str, session: dict[str, Any]) -> dict[str, Any]:
        if "search" in message.lower() and any(t.name == "search" for t in self.tools):
            tool = next(t for t in self.tools if t.name == "search")
            result = tool.run(q=message)
            session.setdefault("events", []).append({"type": "tool", "name": "search", "result": result})
            text = f"Found: {result}"
        else:
            text = f"{self.name}: {message}"
        session.setdefault("events", []).append({"type": "text", "text": text})
        return {"text": text}

@dataclass
class Runner:
    agent: LlmAgent
    def run(self, user_id: str, session_id: str, message: str) -> dict[str, Any]:
        session = {"user_id": user_id, "session_id": session_id, "events": []}
        out = self.agent.step(message, session)
        return {"ok": True, "framework": "google_adk", "output": out["text"], "session": session}

    def stream(self, message: str) -> Iterator[dict[str, Any]]:
        yield {"event": "start"}
        res = self.run("u1", "s1", message)
        yield {"event": "final", "data": res}

def demo_runner() -> Runner:
    return Runner(LlmAgent("helpdesk", "Be helpful", tools=[Tool("search", lambda q: f"hit:{q[:40]}")]))
