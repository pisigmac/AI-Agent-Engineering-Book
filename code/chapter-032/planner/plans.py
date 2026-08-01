"""Planning strategies: plan-and-execute and ReAct-style steps."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Plan:
    goal: str
    steps: list[str]
    strategy: str
    def to_dict(self) -> dict[str, Any]:
        return {"goal": self.goal, "strategy": self.strategy, "steps": self.steps}

class Planner:
    def plan(self, goal: str, *, strategy: str = "plan_execute") -> Plan:
        strategy = strategy.lower().replace("-", "_")
        g = goal.lower()
        if strategy == "react":
            steps = ["thought:analyze", "action:gather", "observe:results", "thought:answer", "final"]
        else:
            steps = ["decompose"]
            if any(k in g for k in ("research", "compare", "multi")):
                steps += ["research_sources", "synthesize"]
            elif any(k in g for k in ("weather", "lookup", "find")):
                steps += ["call_tools", "format"]
            else:
                steps += ["draft", "verify"]
            steps.append("deliver")
        return Plan(goal=goal, steps=steps, strategy=strategy)

@dataclass
class PlanExecutor:
    planner: Planner = field(default_factory=Planner)
    def run(self, goal: str, *, strategy: str = "plan_execute") -> dict[str, Any]:
        plan = self.planner.plan(goal, strategy=strategy)
        trace = []
        for i, step in enumerate(plan.steps):
            trace.append({"i": i, "step": step, "status": "done", "note": f"executed {step}"})
        return {"ok": True, "plan": plan.to_dict(), "trace": trace, "result": f"Completed: {goal}"}
