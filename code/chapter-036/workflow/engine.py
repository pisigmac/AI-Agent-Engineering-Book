"""Workflow orchestration: sequential, parallel, branch, retry policies."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable

StepFn = Callable[[dict[str, Any]], dict[str, Any]]

@dataclass
class Step:
    name: str
    fn: StepFn
    retries: int = 0

@dataclass
class Workflow:
    name: str
    steps: list[Any] = field(default_factory=list)  # Step or list[Step] for parallel

    def add(self, step: Step) -> None:
        self.steps.append(step)
    def add_parallel(self, steps: list[Step]) -> None:
        self.steps.append(steps)

    def run(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(context or {})
        trace: list[dict[str, Any]] = []
        for item in self.steps:
            if isinstance(item, list):
                results = {}
                with ThreadPoolExecutor(max_workers=max(1, len(item))) as pool:
                    futs = {pool.submit(self._run_step, s, dict(ctx)): s.name for s in item}
                    for fut in as_completed(futs):
                        name = futs[fut]
                        results[name] = fut.result()
                ctx["parallel"] = results
                trace.append({"parallel": {k: v.get("ok") for k, v in results.items()}})
                # merge outputs
                for v in results.values():
                    if v.get("ok"):
                        ctx.update(v.get("output") or {})
            else:
                res = self._run_step(item, ctx)
                trace.append({"step": item.name, **{k: res[k] for k in ("ok", "attempts")}})
                if not res["ok"]:
                    return {"ok": False, "context": ctx, "trace": trace, "failed": item.name}
                ctx.update(res.get("output") or {})
        return {"ok": True, "context": ctx, "trace": trace}

    def _run_step(self, step: Step, ctx: dict[str, Any]) -> dict[str, Any]:
        attempts = 0
        last_err = None
        while attempts <= step.retries:
            attempts += 1
            try:
                out = step.fn(ctx)
                return {"ok": True, "output": out, "attempts": attempts}
            except Exception as e:  # noqa: BLE001
                last_err = str(e)
        return {"ok": False, "error": last_err, "attempts": attempts}

def demo_workflow() -> Workflow:
    wf = Workflow("support-ticket")
    wf.add(Step("classify", lambda c: {"intent": "billing" if "refund" in c.get("text","").lower() else "general"}))
    def flaky(c):
        # succeed always for demo but show retry field
        return {"kb_hit": "30-day refund policy"}
    wf.add(Step("retrieve", flaky, retries=1))
    wf.add_parallel([
        Step("safety_check", lambda c: {"safe": True}),
        Step("tone_check", lambda c: {"tone": "professional"}),
    ])
    wf.add(Step("answer", lambda c: {"answer": f"Intent={c.get('intent')}; {c.get('kb_hit')}"}))
    return wf
