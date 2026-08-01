"""Framework execution loop with termination and budgets."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable

Decide = Callable[[str, list[dict[str, Any]]], dict[str, Any]]
Act = Callable[[dict[str, Any]], dict[str, Any]]

@dataclass
class ExecutionLoop:
    decide: Decide
    act: Act
    max_steps: int = 6
    def run(self, goal: str) -> dict[str, Any]:
        hist: list[dict[str, Any]] = []
        for step in range(self.max_steps):
            decision = self.decide(goal, hist)
            hist.append({"step": step, "decision": decision})
            if decision.get("stop"):
                return {"ok": True, "reason": "stop", "result": decision.get("result"), "history": hist}
            obs = self.act(decision.get("action") or {})
            hist.append({"step": step, "obs": obs})
            if obs.get("done"):
                return {"ok": True, "reason": "done", "result": obs.get("result"), "history": hist}
        return {"ok": False, "reason": "max_steps", "history": hist}

def demo_loop() -> ExecutionLoop:
    state = {"n": 0}
    def decide(goal, hist):
        if state["n"] >= 1:
            return {"stop": True, "result": f"done:{goal}"}
        return {"action": {"op": "tick"}}
    def act(action):
        state["n"] += 1
        return {"done": True, "result": "ticked"}
    return ExecutionLoop(decide, act)
