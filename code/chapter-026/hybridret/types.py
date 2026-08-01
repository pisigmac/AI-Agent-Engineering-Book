"""Hybrid retrieval contracts."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any

@dataclass(frozen=True)
class Document:
    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class Hit:
    id: str
    score: float
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    channel: str = ""
    rank: int = 0
    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["score"] = round(float(self.score), 6)
        return d

@dataclass
class EvalReport:
    n_queries: int
    recall_at_k: float
    mrr: float
    per_query: list[dict[str, Any]] = field(default_factory=list)
    def to_dict(self) -> dict[str, Any]:
        return {
            "n_queries": self.n_queries,
            "recall_at_k": round(self.recall_at_k, 4),
            "mrr": round(self.mrr, 4),
            "per_query": self.per_query,
        }
