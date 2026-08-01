"""Choose workflow vs agent vs hybrid for a task."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ModeDecision:
    mode: str  # workflow | agent | hybrid
    reason: str
    confidence: float
    def to_dict(self) -> dict[str, Any]:
        return {"mode": self.mode, "reason": self.reason, "confidence": self.confidence}

def select_mode(task: str, *, needs_tools: bool = False, deterministic: bool = False, open_ended: bool = False) -> ModeDecision:
    t = task.lower()
    if deterministic or any(k in t for k in ("invoice", "etl", "batch", "schedule")):
        return ModeDecision("workflow", "deterministic multi-step process", 0.9)
    if open_ended or any(k in t for k in ("research", "investigate", "explore", "why")):
        return ModeDecision("agent", "open-ended goal requiring autonomy", 0.85)
    if needs_tools or any(k in t for k in ("lookup", "search", "weather", "ticket")):
        return ModeDecision("hybrid", "structured flow with autonomous tool use", 0.8)
    return ModeDecision("hybrid", "default balanced choice", 0.6)

def run_selected(task: str) -> dict[str, Any]:
    d = select_mode(task)
    if d.mode == "workflow":
        result = {"steps": ["validate", "transform", "load"], "output": f"workflow:{task}"}
    elif d.mode == "agent":
        result = {"steps": ["plan", "act", "reflect"], "output": f"agent:{task}"}
    else:
        result = {"steps": ["route", "tool_loop", "finalize"], "output": f"hybrid:{task}"}
    return {"decision": d.to_dict(), "run": result}
