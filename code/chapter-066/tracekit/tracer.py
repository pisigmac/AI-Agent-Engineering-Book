"""Distributed-style tracing with nested spans."""
from __future__ import annotations
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any
import uuid

@dataclass
class Span:
    name: str
    trace_id: str
    span_id: str
    parent_id: str | None = None
    attrs: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    status: str = "ok"
    duration_ms: float = 0.0

@dataclass
class Tracer:
    service: str
    spans: list[Span] = field(default_factory=list)
    def start_span(self, name: str, parent: Span | None = None, **attrs: Any) -> "_SpanCtx":
        return _SpanCtx(self, name, parent, attrs)
    def export(self) -> dict[str, Any]:
        return {
            "service": self.service,
            "spans": [
                {"name": s.name, "trace_id": s.trace_id, "span_id": s.span_id, "parent_id": s.parent_id,
                 "duration_ms": round(s.duration_ms, 3), "status": s.status, "attrs": s.attrs, "events": s.events}
                for s in self.spans
            ],
        }

class _SpanCtx:
    def __init__(self, tracer: Tracer, name: str, parent: Span | None, attrs: dict[str, Any]) -> None:
        self.tracer = tracer
        self.span = Span(
            name=name,
            trace_id=parent.trace_id if parent else uuid.uuid4().hex,
            span_id=uuid.uuid4().hex[:16],
            parent_id=parent.span_id if parent else None,
            attrs=attrs,
        )
        self.t0 = 0.0
    def __enter__(self) -> Span:
        self.t0 = perf_counter(); return self.span
    def __exit__(self, exc_type, exc, tb) -> bool:
        self.span.duration_ms = (perf_counter() - self.t0) * 1000
        if exc:
            self.span.status = "error"
            self.span.events.append({"exception": str(exc)})
        self.tracer.spans.append(self.span)
        return False

def demo_trace() -> dict[str, Any]:
    tr = Tracer("agent-api")
    with tr.start_span("handle_request", http_path="/v1/chat") as root:
        with tr.start_span("retrieve", root):
            pass
        with tr.start_span("generate", root) as g:
            g.events.append({"tokens": 12})
    return tr.export()
