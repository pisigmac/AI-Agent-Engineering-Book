"""Contracts for the mini vector database."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class IndexType(str, Enum):
    FLAT = "flat"  # exact linear scan
    IVF = "ivf"  # inverted file (coarse clusters)


@dataclass(frozen=True)
class VectorRecord:
    id: str
    vector: tuple[float, ...]
    metadata: dict[str, Any] = field(default_factory=dict)
    text: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id required")
        if not self.vector:
            raise ValueError("vector required")


@dataclass(frozen=True)
class QueryHit:
    id: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)
    text: str = ""
    rank: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "id": self.id,
            "score": round(self.score, 6),
            "metadata": self.metadata,
            "text": self.text,
        }


@dataclass
class QueryResult:
    collection: str
    hits: list[QueryHit]
    index_type: str
    n_scanned: int
    took_ms: float
    filters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "collection": self.collection,
            "index_type": self.index_type,
            "n_scanned": self.n_scanned,
            "took_ms": round(self.took_ms, 3),
            "filters": self.filters,
            "hits": [h.to_dict() for h in self.hits],
        }


@dataclass
class CollectionStats:
    name: str
    count: int
    dimensions: int | None
    index_type: str
    model_id: str
    metadata_keys: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
