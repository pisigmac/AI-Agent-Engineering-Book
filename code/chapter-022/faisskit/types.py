"""Contracts for FAISS-backed indexes and PDF search."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class IndexKind(str, Enum):
    FLAT_IP = "flat_ip"  # exact inner product (cosine if L2-normalized)
    FLAT_L2 = "flat_l2"
    IVF_FLAT = "ivf_flat"
    HNSW = "hnsw"


@dataclass(frozen=True)
class IndexedDoc:
    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchHit:
    id: str
    score: float
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    rank: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "id": self.id,
            "score": round(float(self.score), 6),
            "text": self.text,
            "metadata": self.metadata,
        }


@dataclass
class SearchResult:
    hits: list[SearchHit]
    index_kind: str
    ntotal: int
    took_ms: float
    query: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "index_kind": self.index_kind,
            "ntotal": self.ntotal,
            "took_ms": round(self.took_ms, 3),
            "hits": [h.to_dict() for h in self.hits],
        }


@dataclass
class IndexStats:
    kind: str
    dimensions: int
    ntotal: int
    metric: str
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
