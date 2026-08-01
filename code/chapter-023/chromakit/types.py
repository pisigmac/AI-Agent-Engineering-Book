"""Contracts for Chroma-style collections and the knowledge assistant."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class QueryHit:
    id: str
    document: str
    metadata: dict[str, Any] = field(default_factory=dict)
    distance: float | None = None
    rank: int = 0

    @property
    def score(self) -> float:
        """Higher is better. Chroma returns distance (lower better) for L2/cosine variants."""
        if self.distance is None:
            return 0.0
        # Convert distance to a similarity-like score for display
        return 1.0 / (1.0 + max(self.distance, 0.0))

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "id": self.id,
            "document": self.document,
            "metadata": self.metadata,
            "distance": None if self.distance is None else round(float(self.distance), 6),
            "score": round(self.score, 6),
        }


@dataclass
class QueryResult:
    collection: str
    hits: list[QueryHit]
    backend: str
    query: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "collection": self.collection,
            "backend": self.backend,
            "query": self.query,
            "hits": [h.to_dict() for h in self.hits],
        }


@dataclass
class AssistantAnswer:
    answer: str
    citations: list[dict[str, Any]]
    grounded: bool
    query: str
    collection: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
