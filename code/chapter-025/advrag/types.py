"""Contracts for advanced RAG / enterprise search."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Document:
    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    parent_id: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id required")


@dataclass(frozen=True)
class SearchHit:
    id: str
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)
    parent_id: str | None = None
    sources: tuple[str, ...] = ()  # e.g. ("bm25", "dense")
    rank: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "id": self.id,
            "score": round(self.score, 6),
            "text": self.text,
            "metadata": self.metadata,
            "parent_id": self.parent_id,
            "sources": list(self.sources),
        }


@dataclass
class SearchResponse:
    query: str
    hits: list[SearchHit]
    expanded_queries: list[str] = field(default_factory=list)
    strategy: str = "hybrid"
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "strategy": self.strategy,
            "expanded_queries": self.expanded_queries,
            "hits": [h.to_dict() for h in self.hits],
            "diagnostics": self.diagnostics,
        }
