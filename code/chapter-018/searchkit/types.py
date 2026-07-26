"""Contracts for the semantic search engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Document:
    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    title: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Document.id required")
        if not isinstance(self.text, str):
            raise TypeError("text must be str")


@dataclass(frozen=True)
class VectorRecord:
    id: str
    vector: tuple[float, ...]
    text: str
    metadata: dict[str, Any]
    model_id: str
    dim: int
    title: str = ""

    def __post_init__(self) -> None:
        if self.dim != len(self.vector):
            raise ValueError("dim mismatch")


@dataclass(frozen=True)
class SearchHit:
    id: str
    score: float
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    title: str = ""
    rank: int = 0
    score_components: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "id": self.id,
            "score": round(self.score, 6),
            "title": self.title,
            "text": self.text,
            "metadata": self.metadata,
            "score_components": {k: round(v, 6) for k, v in self.score_components.items()},
        }


@dataclass
class SearchResponse:
    query: str
    hits: list[SearchHit]
    model_id: str
    index_size: int
    filters: dict[str, Any] = field(default_factory=dict)
    took_ms: float = 0.0
    strategy: str = "cosine"

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "model_id": self.model_id,
            "index_size": self.index_size,
            "strategy": self.strategy,
            "filters": self.filters,
            "took_ms": round(self.took_ms, 3),
            "hits": [h.to_dict() for h in self.hits],
        }


@dataclass(frozen=True)
class LabeledQuery:
    query: str
    relevant_ids: tuple[str, ...]
    description: str = ""


@dataclass
class EvalReport:
    n_queries: int
    recall_at_k: float
    mrr: float
    precision_at_k: float
    per_query: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_queries": self.n_queries,
            "recall_at_k": round(self.recall_at_k, 4),
            "mrr": round(self.mrr, 4),
            "precision_at_k": round(self.precision_at_k, 4),
            "per_query": self.per_query,
        }
