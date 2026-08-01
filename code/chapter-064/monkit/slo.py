"""SLOs, error budget, and simple alert evaluation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class SLO:
    name: str
    target: float  # e.g. 0.99
    window_requests: int = 0
    window_errors: int = 0
    def record(self, *, ok: bool) -> None:
        self.window_requests += 1
        if not ok:
            self.window_errors += 1
    @property
    def availability(self) -> float:
        if self.window_requests == 0:
            return 1.0
        return 1.0 - (self.window_errors / self.window_requests)
    @property
    def error_budget_remaining(self) -> float:
        # remaining fraction of allowed error budget
        allowed = 1.0 - self.target
        used = 1.0 - self.availability
        if allowed <= 0:
            return 0.0
        return max(0.0, 1.0 - used / allowed)

@dataclass
class Alert:
    name: str
    severity: str
    message: str

@dataclass
class Monitor:
    slos: list[SLO] = field(default_factory=list)
    def evaluate(self) -> list[Alert]:
        alerts = []
        for slo in self.slos:
            if slo.availability < slo.target:
                alerts.append(Alert(slo.name, "page", f"SLO burn: avail={slo.availability:.4f} < {slo.target}"))
            elif slo.error_budget_remaining < 0.2:
                alerts.append(Alert(slo.name, "ticket", f"error budget low: {slo.error_budget_remaining:.2%}"))
        return alerts
    def dashboard(self) -> dict[str, Any]:
        return {
            "slos": [
                {"name": s.name, "target": s.target, "availability": round(s.availability, 4),
                 "budget_remaining": round(s.error_budget_remaining, 4), "n": s.window_requests}
                for s in self.slos
            ],
            "alerts": [a.__dict__ for a in self.evaluate()],
        }
