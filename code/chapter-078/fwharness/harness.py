"""Framework agent harness: lifecycle, isolation context, hooks."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

AgentFn = Callable[[str, dict[str, Any]], dict[str, Any]]

@dataclass
class Harness:
    agent: AgentFn
    max_steps: int = 5
    hooks: list[Callable[[dict[str, Any]], None]] = field(default_factory=list)
    def run(self, goal: str) -> dict[str, Any]:
        ctx: dict[str, Any] = {"isolated": True, "goal": goal}
        history = []
        for step in range(1, self.max_steps + 1):
            out = self.agent(goal, {**ctx, "step": step})
            history.append(out)
            for h in self.hooks:
                h({"step": step, "out": out})
            ctx.update(out.get("state") or {})
            if out.get("done"):
                return {"ok": True, "result": out.get("result"), "history": history, "lifecycle": "succeeded"}
        return {"ok": False, "result": None, "history": history, "lifecycle": "max_steps"}
