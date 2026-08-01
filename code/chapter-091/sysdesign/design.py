"""System design calculators and interview-style design scaffolding."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import math


@dataclass
class CapacityEstimate:
    qps: float
    daily_requests: float
    storage_gb_year: float
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "qps": round(self.qps, 3),
            "daily_requests": int(self.daily_requests),
            "storage_gb_year": round(self.storage_gb_year, 3),
            "notes": list(self.notes),
        }


def estimate_capacity(
    *,
    dau: int,
    requests_per_user_day: float,
    avg_payload_kb: float,
    retention_days: int = 365,
    peak_multiplier: float = 3.0,
) -> CapacityEstimate:
    """Back-of-envelope capacity for an AI product surface."""
    if dau < 0 or requests_per_user_day < 0 or avg_payload_kb < 0:
        raise ValueError("inputs must be non-negative")
    daily = dau * requests_per_user_day
    avg_qps = daily / 86_400.0
    peak_qps = avg_qps * peak_multiplier
    storage_gb = (daily * avg_payload_kb * retention_days) / (1024.0 * 1024.0)
    notes = [
        f"avg_qps={avg_qps:.3f}, design_for_peak_qps={peak_qps:.3f}",
        "Separate online inference path from batch/index rebuild jobs",
        "Budget LLM tokens separately from request QPS",
    ]
    return CapacityEstimate(
        qps=peak_qps,
        daily_requests=daily,
        storage_gb_year=storage_gb,
        notes=notes,
    )


@dataclass
class LatencyBudget:
    """Milliseconds budget breakdown for an agent request path."""

    total_ms: int
    parts: dict[str, int]  # name -> ms

    def remaining(self) -> int:
        return self.total_ms - sum(self.parts.values())

    def valid(self) -> bool:
        return self.remaining() >= 0 and all(v >= 0 for v in self.parts.values())

    def as_dict(self) -> dict[str, Any]:
        return {
            "total_ms": self.total_ms,
            "parts": dict(self.parts),
            "remaining_ms": self.remaining(),
            "valid": self.valid(),
        }


DEFAULT_CHECKLIST = [
    "Clarify requirements and non-goals",
    "Estimate scale (QPS, storage, cost)",
    "Draw high-level architecture",
    "Deep-dive critical path (RAG / tools / multi-agent)",
    "Data model and consistency",
    "Failure modes and retries",
    "Observability and evaluation gates",
    "Security, tenancy, and abuse",
    "Cost and model routing",
    "Rollout, canaries, and rollback",
]


@dataclass
class DesignChecklist:
    items: list[str] = field(default_factory=lambda: list(DEFAULT_CHECKLIST))
    done: set[str] = field(default_factory=set)

    def mark(self, item: str) -> None:
        if item not in self.items:
            raise KeyError(item)
        self.done.add(item)

    def progress(self) -> dict[str, Any]:
        return {
            "total": len(self.items),
            "done": len(self.done),
            "pct": round(100.0 * len(self.done) / max(1, len(self.items)), 1),
            "remaining": [i for i in self.items if i not in self.done],
        }


@dataclass
class SystemDesignKit:
    """Compose capacity + latency + checklist into a design brief."""

    title: str
    checklist: DesignChecklist = field(default_factory=DesignChecklist)

    def brief(
        self,
        *,
        dau: int,
        requests_per_user_day: float,
        avg_payload_kb: float,
        latency: LatencyBudget,
    ) -> dict[str, Any]:
        cap = estimate_capacity(
            dau=dau,
            requests_per_user_day=requests_per_user_day,
            avg_payload_kb=avg_payload_kb,
        )
        return {
            "title": self.title,
            "capacity": cap.as_dict(),
            "latency": latency.as_dict(),
            "checklist": self.checklist.progress(),
            "components_hint": [
                "API gateway + auth",
                "Orchestrator / agent loop",
                "Tool adapters",
                "Vector/index store",
                "LLM gateway with budgets",
                "Eval + observability",
            ],
        }
