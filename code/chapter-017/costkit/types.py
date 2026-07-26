"""Shared contracts for cost, usage, and performance telemetry."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class CallKind(str, Enum):
    CHAT = "chat"
    EMBED = "embed"
    TOOL = "tool"
    OTHER = "other"


class CacheOutcome(str, Enum):
    MISS = "miss"
    HIT = "hit"
    BYPASS = "bypass"


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0

    def __post_init__(self) -> None:
        if self.input_tokens < 0 or self.output_tokens < 0:
            raise ValueError("token counts must be non-negative")

    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            self.input_tokens + other.input_tokens,
            self.output_tokens + other.output_tokens,
        )


@dataclass(frozen=True)
class ModelPrice:
    """USD per 1M tokens — replace with contract rates in production."""

    model_id: str
    input_per_mtok: float
    output_per_mtok: float
    notes: str = ""

    def cost_usd(self, usage: TokenUsage) -> float:
        return (
            usage.input_tokens / 1_000_000.0 * self.input_per_mtok
            + usage.output_tokens / 1_000_000.0 * self.output_per_mtok
        )


@dataclass
class UsageEvent:
    """One billable (or cache-saved) model interaction."""

    model_id: str
    usage: TokenUsage
    cost_usd: float
    latency_ms: float
    kind: CallKind = CallKind.CHAT
    cache: CacheOutcome = CacheOutcome.MISS
    request_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "input_tokens": self.usage.input_tokens,
            "output_tokens": self.usage.output_tokens,
            "cost_usd": self.cost_usd,
            "latency_ms": self.latency_ms,
            "kind": self.kind.value,
            "cache": self.cache.value,
            "request_id": self.request_id,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class Budget:
    """Hard and soft spend / token limits for a window."""

    max_cost_usd: float | None = None
    max_input_tokens: int | None = None
    max_output_tokens: int | None = None
    max_calls: int | None = None
    name: str = "default"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BudgetStatus:
    budget: Budget
    spent_usd: float
    input_tokens: int
    output_tokens: int
    calls: int
    ok: bool
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "budget": self.budget.to_dict(),
            "spent_usd": self.spent_usd,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "calls": self.calls,
            "ok": self.ok,
            "violations": self.violations,
        }


@dataclass
class DashboardSnapshot:
    total_cost_usd: float
    total_calls: int
    cache_hits: int
    cache_misses: int
    total_input_tokens: int
    total_output_tokens: int
    avg_latency_ms: float
    cost_by_model: dict[str, float]
    calls_by_model: dict[str, int]
    saved_cost_usd_estimate: float
    recommendations: list[str] = field(default_factory=list)

    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total) if total else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_cost_usd": round(self.total_cost_usd, 8),
            "total_calls": self.total_calls,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": round(self.cache_hit_rate, 4),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "avg_latency_ms": round(self.avg_latency_ms, 3),
            "cost_by_model": {k: round(v, 8) for k, v in self.cost_by_model.items()},
            "calls_by_model": dict(self.calls_by_model),
            "saved_cost_usd_estimate": round(self.saved_cost_usd_estimate, 8),
            "recommendations": list(self.recommendations),
        }
