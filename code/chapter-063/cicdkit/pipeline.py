"""CI/CD pipeline definition and local runner with gates."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

StepFn = Callable[[], dict[str, Any]]

@dataclass
class Step:
    name: str
    fn: StepFn
    gate: bool = False  # must pass

@dataclass
class Pipeline:
    name: str
    steps: list[Step] = field(default_factory=list)
    def add(self, step: Step) -> None:
        self.steps.append(step)
    def run(self) -> dict[str, Any]:
        results = []
        for step in self.steps:
            try:
                out = step.fn()
                ok = bool(out.get("ok", True))
            except Exception as e:  # noqa: BLE001
                ok, out = False, {"error": str(e)}
            results.append({"step": step.name, "ok": ok, "out": out, "gate": step.gate})
            if step.gate and not ok:
                return {"ok": False, "failed_gate": step.name, "results": results}
        return {"ok": True, "results": results}

def demo_pipeline() -> Pipeline:
    p = Pipeline("agent-ci")
    p.add(Step("lint", lambda: {"ok": True}))
    p.add(Step("unit", lambda: {"ok": True, "tests": 12}, gate=True))
    p.add(Step("eval", lambda: {"ok": True, "pass_rate": 0.95}, gate=True))
    p.add(Step("build_image", lambda: {"ok": True, "tag": "1.0.0"}))
    p.add(Step("deploy_staging", lambda: {"ok": True}))
    return p
