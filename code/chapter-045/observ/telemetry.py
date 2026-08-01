"""Lightweight observability: structured logs, metrics counters, span traces."""
from __future__ import annotations
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

@dataclass
class Span:
    name: str
    attrs: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    status: str = "ok"
    duration_ms: float = 0.0

@dataclass
class Telemetry:
    logs: list[dict[str, Any]] = field(default_factory=list)
    counters: dict[str, float] = field(default_factory=dict)
    spans: list[Span] = field(default_factory=list)

    def log(self, level: str, msg: str, **fields: Any) -> None:
        self.logs.append({"level": level, "msg": msg, **fields})

    def incr(self, name: str, value: float = 1.0) -> None:
        self.counters[name] = self.counters.get(name, 0.0) + value

    def span(self, name: str, **attrs: Any):
        return _SpanCtx(self, name, attrs)

    def export(self) -> dict[str, Any]:
        return {
            "logs": self.logs,
            "metrics": self.counters,
            "traces": [
                {"name": s.name, "duration_ms": round(s.duration_ms, 3), "status": s.status, "attrs": s.attrs, "events": s.events}
                for s in self.spans
            ],
        }

class _SpanCtx:
    def __init__(self, tel: Telemetry, name: str, attrs: dict[str, Any]) -> None:
        self.tel = tel
        self.span = Span(name=name, attrs=attrs)
        self.t0 = 0.0
    def __enter__(self):
        self.t0 = perf_counter()
        return self.span
    def __exit__(self, exc_type, exc, tb):
        self.span.duration_ms = (perf_counter() - self.t0) * 1000
        if exc:
            self.span.status = "error"
            self.span.events.append({"error": str(exc)})
            self.tel.incr("span.errors")
        self.tel.spans.append(self.span)
        self.tel.incr("span.count")
        return False

def traced_agent_run(goal: str) -> dict[str, Any]:
    tel = Telemetry()
    tel.log("info", "start", goal=goal)
    with tel.span("retrieve", goal=goal) as sp:
        sp.events.append({"hits": 2})
        tel.incr("retrieve.hits", 2)
    with tel.span("generate"):
        answer = f"answer:{goal}"
        tel.incr("tokens", 42)
    tel.log("info", "done")
    return {"answer": answer, "telemetry": tel.export()}
