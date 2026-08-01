"""Plan objects with optional replan on failure."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Plan:
    goal: str
    steps: list[str]
    version: int = 1
    def to_dict(self) -> dict[str, Any]:
        return {"goal": self.goal, "steps": self.steps, "version": self.version}

class Planner:
    def make(self, goal: str) -> Plan:
        g = goal.lower()
        steps = ["understand"]
        if any(k in g for k in ("search", "research", "find")):
            steps += ["search", "synthesize"]
        else:
            steps += ["draft"]
        steps.append("verify")
        return Plan(goal, steps)
    def replan(self, plan: Plan, failure: str) -> Plan:
        steps = list(plan.steps)
        if "search" not in steps:
            steps.insert(1, "search")
        steps.append(f"recover:{failure[:20]}")
        return Plan(plan.goal, steps, version=plan.version + 1)
