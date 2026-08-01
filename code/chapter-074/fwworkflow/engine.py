"""Workflow engine with sequential steps and retry policy."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class Step:
    name: str
    fn: Callable[[dict[str, Any]], dict[str, Any]]
    retries: int = 0

@dataclass
class WorkflowEngine:
    steps: list[Step] = field(default_factory=list)
    def add(self, step: Step) -> None:
        self.steps.append(step)
    def run(self, ctx: dict[str, Any] | None = None) -> dict[str, Any]:
        state = dict(ctx or {})
        trace = []
        for step in self.steps:
            attempts = 0
            while True:
                attempts += 1
                try:
                    out = step.fn(state)
                    state.update(out)
                    trace.append({"step": step.name, "ok": True, "attempts": attempts})
                    break
                except Exception as e:  # noqa: BLE001
                    if attempts > step.retries:
                        return {"ok": False, "failed": step.name, "error": str(e), "trace": trace, "state": state}
            # continue
        return {"ok": True, "state": state, "trace": trace}
