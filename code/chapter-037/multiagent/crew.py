"""Multi-agent research assistant: planner, researcher, writer, reviewer."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class Agent:
    role: str
    run: Callable[[dict[str, Any]], dict[str, Any]]

@dataclass
class MultiAgentSystem:
    agents: dict[str, Agent] = field(default_factory=dict)
    def add(self, agent: Agent) -> None:
        self.agents[agent.role] = agent
    def run(self, goal: str) -> dict[str, Any]:
        state: dict[str, Any] = {"goal": goal, "trace": []}
        order = ["planner", "researcher", "writer", "reviewer"]
        for role in order:
            if role not in self.agents:
                continue
            out = self.agents[role].run(state)
            state.update(out)
            state["trace"].append({"role": role, "keys": list(out.keys())})
        # consensus: reviewer may request rewrite once
        if state.get("needs_revision") and "writer" in self.agents:
            out = self.agents["writer"].run(state)
            state.update(out)
            state["trace"].append({"role": "writer", "keys": list(out.keys()), "revision": True})
            out = self.agents["reviewer"].run(state)
            state.update(out)
            state["trace"].append({"role": "reviewer", "keys": list(out.keys()), "final": True})
        return {
            "ok": True,
            "goal": goal,
            "plan": state.get("plan"),
            "notes": state.get("notes"),
            "draft": state.get("draft"),
            "review": state.get("review"),
            "final": state.get("draft"),
            "trace": state.get("trace"),
        }

def research_assistant() -> MultiAgentSystem:
    mas = MultiAgentSystem()
    mas.add(Agent("planner", lambda s: {"plan": [f"research:{s['goal']}", "outline", "write", "review"]}))
    mas.add(Agent("researcher", lambda s: {"notes": [f"fact about {s['goal']}", "counterpoint", "source:kb"]}))
    mas.add(Agent("writer", lambda s: {"draft": f"# {s['goal']}\n\n" + "\n".join(f"- {n}" for n in s.get("notes", [])), "needs_revision": False}))
    def review(s):
        draft = s.get("draft", "")
        ok = len(draft) > 20 and "fact" in draft
        return {"review": "approve" if ok else "revise", "needs_revision": not ok, "confidence": 0.8 if ok else 0.4}
    mas.add(Agent("reviewer", review))
    return mas
