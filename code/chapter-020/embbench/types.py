"""Contracts for embedding model catalog and benchmarks."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Protocol, Sequence, runtime_checkable


class Provider(str, Enum):
    OPENAI = "openai"
    COHERE = "cohere"
    VOYAGE = "voyage"
    LOCAL = "local"
    TEACHING = "teaching"
    OTHER = "other"


class ModelFamily(str, Enum):
    API = "api"
    OPEN_WEIGHTS = "open_weights"
    LEXICAL = "lexical"
    HASHING = "hashing"


@dataclass(frozen=True)
class EmbeddingModelCard:
    """Catalog entry for an embedding model (illustrative specs)."""

    model_id: str
    display_name: str
    provider: Provider
    family: ModelFamily
    dimensions: int
    max_tokens: int
    cost_per_1m_tokens: float  # USD, illustrative
    multilingual: bool
    supports_instructions: bool = False
    latency_class: str = "standard"  # fast | standard | slow
    notes: str = ""
    languages: tuple[str, ...] = ("en",)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["provider"] = self.provider.value
        d["family"] = self.family.value
        d["languages"] = list(self.languages)
        return d


@runtime_checkable
class Embedder(Protocol):
    model_id: str
    dimensions: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        ...


@dataclass(frozen=True)
class LabeledPair:
    query: str
    positive: str
    negatives: tuple[str, ...] = ()
    lang: str = "en"
    tag: str = ""


@dataclass
class ModelBenchResult:
    model_id: str
    dimensions: int
    recall_at_1: float
    recall_at_3: float
    mrr: float
    multilingual_recall_at_1: float
    avg_latency_ms: float
    est_cost_per_1k_queries_usd: float
    storage_bytes_per_1k_docs: int
    n_pairs: int
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "dimensions": self.dimensions,
            "recall_at_1": round(self.recall_at_1, 4),
            "recall_at_3": round(self.recall_at_3, 4),
            "mrr": round(self.mrr, 4),
            "multilingual_recall_at_1": round(self.multilingual_recall_at_1, 4),
            "avg_latency_ms": round(self.avg_latency_ms, 3),
            "est_cost_per_1k_queries_usd": round(self.est_cost_per_1k_queries_usd, 6),
            "storage_bytes_per_1k_docs": self.storage_bytes_per_1k_docs,
            "n_pairs": self.n_pairs,
            "notes": self.notes,
        }


@dataclass
class CompareReport:
    results: list[ModelBenchResult]
    ranking_by_mrr: list[str]
    ranking_by_cost_efficiency: list[str]
    recommendation: str
    rationale: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "results": [r.to_dict() for r in self.results],
            "ranking_by_mrr": self.ranking_by_mrr,
            "ranking_by_cost_efficiency": self.ranking_by_cost_efficiency,
            "recommendation": self.recommendation,
            "rationale": self.rationale,
        }
