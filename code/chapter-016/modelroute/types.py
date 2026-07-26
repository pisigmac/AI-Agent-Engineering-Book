"""Contracts for model catalog, tasks, and routing decisions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    META = "meta"
    MISTRAL = "mistral"
    LOCAL = "local"
    OTHER = "other"


class QualityTier(str, Enum):
    """Relative quality band — not a leaderboard claim."""

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    FLAGSHIP = "flagship"


class LatencyClass(str, Enum):
    FAST = "fast"
    STANDARD = "standard"
    SLOW = "slow"


class TaskKind(str, Enum):
    CHAT = "chat"
    CLASSIFY = "classify"
    EXTRACT = "extract"
    SUMMARIZE = "summarize"
    CODE = "code"
    TOOL_PLAN = "tool_plan"
    REASONING = "reasoning"
    EMBED = "embed"
    CREATIVE = "creative"


class RouteStrategy(str, Enum):
    COST = "cost"
    LATENCY = "latency"
    QUALITY = "quality"
    BALANCED = "balanced"
    PINNED = "pinned"


@dataclass(frozen=True)
class ModelCapabilities:
    chat: bool = True
    tools: bool = False
    json_mode: bool = False
    vision: bool = False
    long_context: bool = False
    code: bool = False
    embeddings: bool = False
    open_weights: bool = False

    def supports(self, kind: TaskKind) -> bool:
        if kind is TaskKind.EMBED:
            return self.embeddings
        if kind is TaskKind.CODE:
            return self.code or self.chat
        if kind is TaskKind.TOOL_PLAN:
            return self.tools or self.chat
        if kind is TaskKind.EXTRACT:
            return self.json_mode or self.chat
        return self.chat


@dataclass(frozen=True)
class ModelProfile:
    """Catalog entry for a generation or embedding model.

    Cost numbers are illustrative unit prices for teaching (per 1M tokens).
    Replace with live pricing tables in production.
    """

    model_id: str
    display_name: str
    provider: Provider
    quality: QualityTier
    latency: LatencyClass
    context_window: int
    input_cost_per_1m: float
    output_cost_per_1m: float
    capabilities: ModelCapabilities = field(default_factory=ModelCapabilities)
    max_output_tokens: int = 4096
    tags: tuple[str, ...] = ()
    notes: str = ""

    def estimated_cost_usd(
        self,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        return (
            input_tokens / 1_000_000.0 * self.input_cost_per_1m
            + output_tokens / 1_000_000.0 * self.output_cost_per_1m
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["provider"] = self.provider.value
        d["quality"] = self.quality.value
        d["latency"] = self.latency.value
        d["capabilities"] = asdict(self.capabilities)
        d["tags"] = list(self.tags)
        return d


@dataclass(frozen=True)
class TaskRequest:
    """What the platform wants a model to do."""

    kind: TaskKind
    prompt: str
    expected_input_tokens: int = 500
    expected_output_tokens: int = 300
    require_tools: bool = False
    require_json: bool = False
    require_vision: bool = False
    require_long_context: bool = False
    max_latency_ms: int | None = None
    max_cost_usd: float | None = None
    min_quality: QualityTier | None = None
    pinned_model_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.kind, TaskKind):
            object.__setattr__(self, "kind", TaskKind(self.kind))
        if self.min_quality is not None and not isinstance(self.min_quality, QualityTier):
            object.__setattr__(self, "min_quality", QualityTier(self.min_quality))
        if self.expected_input_tokens < 0 or self.expected_output_tokens < 0:
            raise ValueError("token estimates must be non-negative")


@dataclass(frozen=True)
class ScoreBreakdown:
    quality: float
    cost: float
    latency: float
    capability_fit: float
    total: float
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "quality": self.quality,
            "cost": self.cost,
            "latency": self.latency,
            "capability_fit": self.capability_fit,
            "total": self.total,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class RouteCandidate:
    model: ModelProfile
    score: ScoreBreakdown
    eligible: bool
    reject_reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model.model_id,
            "eligible": self.eligible,
            "reject_reasons": list(self.reject_reasons),
            "score": self.score.to_dict() if self.eligible else None,
            "est_cost_usd": round(
                self.model.estimated_cost_usd(
                    # placeholder; filled by router when known
                    0,
                    0,
                ),
                6,
            ),
        }


@dataclass(frozen=True)
class RouteDecision:
    """Authoritative choice for one task request."""

    selected_model_id: str
    strategy: RouteStrategy
    candidates: tuple[RouteCandidate, ...]
    fallback_chain: tuple[str, ...]
    est_cost_usd: float
    est_latency_class: LatencyClass
    reasons: tuple[str, ...]
    task_kind: TaskKind

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_model_id": self.selected_model_id,
            "strategy": self.strategy.value,
            "task_kind": self.task_kind.value,
            "est_cost_usd": self.est_cost_usd,
            "est_latency_class": self.est_latency_class.value,
            "fallback_chain": list(self.fallback_chain),
            "reasons": list(self.reasons),
            "candidates": [
                {
                    "model_id": c.model.model_id,
                    "eligible": c.eligible,
                    "reject_reasons": list(c.reject_reasons),
                    "score": c.score.to_dict() if c.eligible else None,
                }
                for c in self.candidates
            ],
        }


@dataclass
class CompletionResult:
    text: str
    model_id: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost_usd: float
    fallback_used: bool = False
    attempts: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "model_id": self.model_id,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "latency_ms": self.latency_ms,
            "cost_usd": self.cost_usd,
            "fallback_used": self.fallback_used,
            "attempts": self.attempts,
        }


QUALITY_RANK: dict[QualityTier, int] = {
    QualityTier.SMALL: 1,
    QualityTier.MEDIUM: 2,
    QualityTier.LARGE: 3,
    QualityTier.FLAGSHIP: 4,
}

LATENCY_RANK: dict[LatencyClass, int] = {
    LatencyClass.FAST: 1,
    LatencyClass.STANDARD: 2,
    LatencyClass.SLOW: 3,
}
