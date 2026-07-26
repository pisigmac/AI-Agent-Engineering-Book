"""Shared contracts for embedding and semantic search."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Document:
    """A unit of text to embed and index."""

    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Document.id must be non-empty")
        if not isinstance(self.text, str):
            raise TypeError("Document.text must be str")


@dataclass(frozen=True)
class VectorRecord:
    """Stored embedding plus provenance."""

    id: str
    vector: tuple[float, ...]
    text: str
    metadata: dict[str, Any]
    model_id: str
    dim: int

    def __post_init__(self) -> None:
        if self.dim != len(self.vector):
            raise ValueError(f"dim {self.dim} != len(vector) {len(self.vector)}")
        if not self.model_id:
            raise ValueError("model_id required")


@dataclass(frozen=True)
class SearchHit:
    """Ranked neighbor returned to callers / context packing."""

    id: str
    score: float
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    model_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "score": self.score,
            "text": self.text,
            "metadata": self.metadata,
            "model_id": self.model_id,
        }
