"""Agent harness: budgets, recovery, state snapshot, eval hooks."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

AgentFn = Callable[[str, dict[str, Any]], dict[str, Any]]

@dataclass
class Budget:
    max_steps: int = 8
    max_cost_usd: float = 1.0
    max_seconds: float = 30.0

@dataclass
class HarnessState:
    step: int = 0
    cost_usd: float = 0.0
    status: str = "idle"
    last_error: str | None = None
    snapshots: list[dict[str, Any]] = field(default_factory=list)

@dataclass
class AgentHarness:
    agent: AgentFn
    budget: Budget = field(default_factory=Budget)
    on_step: list[Callable[[dict[str, Any]], None]] = field(default_factory=list)
    state: HarnessState = field(default_factory=HarnessState)

    def run(self, goal: str, *, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(context or {})
        self.state = HarnessState(status="running")
        history: list[dict[str, Any]] = []
        while self.state.step < self.budget.max_steps:
            if self.state.cost_usd >= self.budget.max_cost_usd:
                self.state.status = "budget_exceeded"
                break
            self.state.step += 1
            try:
                out = self.agent(goal, {**ctx, "step": self.state.step, "history": history})
            except Exception as e:  # noqa: BLE001
                self.state.last_error = str(e)
                self.state.status = "recovering"
                history.append({"step": self.state.step, "error": str(e)})
                self.state.snapshots.append({"step": self.state.step, "error": str(e)})
                # one recovery attempt: continue
                if self.state.step >= self.budget.max_steps:
                    self.state.status = "failed"
                    break
                continue
            cost = float(out.get("cost_usd", 0.05))
            self.state.cost_usd += cost
            history.append({"step": self.state.step, "out": out})
            snap = {"step": self.state.step, "status": out.get("status"), "cost": self.state.cost_usd}
            self.state.snapshots.append(snap)
            for hook in self.on_step:
                hook(snap)
            ctx.update(out.get("state") or {})
            if out.get("done"):
                self.state.status = "succeeded"
                return {"ok": True, "result": out.get("result"), "history": history, "harness": self._meta()}
        if self.state.status == "running":
            self.state.status = "max_steps"
        return {"ok": False, "result": None, "history": history, "harness": self._meta()}

    def _meta(self) -> dict[str, Any]:
        return {
            "status": self.state.status,
            "steps": self.state.step,
            "cost_usd": round(self.state.cost_usd, 4),
            "last_error": self.state.last_error,
            "checkpoints": len(self.state.snapshots),
        }

def demo_agent(goal: str, ctx: dict[str, Any]) -> dict[str, Any]:
    step = int(ctx.get("step", 1))
    if step == 1:
        return {"status": "thinking", "state": {"plan": ["lookup", "answer"]}, "cost_usd": 0.02}
    if step == 2:
        return {"status": "acting", "state": {"evidence": f"fact about {goal}"}, "cost_usd": 0.03}
    return {"done": True, "result": f"Answer for {goal}: {ctx.get('evidence','n/a')}", "cost_usd": 0.04}
