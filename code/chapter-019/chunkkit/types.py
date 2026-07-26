"""Contracts for document chunking."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ChunkStrategy(str, Enum):
    FIXED = "fixed"
    RECURSIVE = "recursive"
    SLIDING = "sliding"
    SEMANTIC = "semantic"
    HIERARCHICAL = "hierarchical"


@dataclass(frozen=True)
class SourceDocument:
    """A long document before chunking."""

    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    title: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id required")
        if not isinstance(self.text, str):
            raise TypeError("text must be str")


@dataclass(frozen=True)
class Chunk:
    """A span of source text ready to embed/index."""

    id: str
    doc_id: str
    text: str
    start: int
    end: int
    strategy: str
    index: int = 0
    parent_id: str | None = None
    level: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    token_estimate: int = 0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


@dataclass
class ChunkReport:
    doc_id: str
    strategy: str
    n_chunks: int
    avg_chars: float
    avg_tokens_est: float
    min_chars: int
    max_chars: int
    chunks: list[Chunk] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, *, include_text: bool = True) -> dict[str, Any]:
        rows = []
        for c in self.chunks:
            row = c.to_dict()
            if not include_text:
                row.pop("text", None)
            rows.append(row)
        return {
            "doc_id": self.doc_id,
            "strategy": self.strategy,
            "n_chunks": self.n_chunks,
            "avg_chars": round(self.avg_chars, 2),
            "avg_tokens_est": round(self.avg_tokens_est, 2),
            "min_chars": self.min_chars,
            "max_chars": self.max_chars,
            "extras": self.extras,
            "chunks": rows,
        }


@dataclass
class CompareReport:
    doc_id: str
    strategies: dict[str, dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {"doc_id": self.doc_id, "strategies": self.strategies}
