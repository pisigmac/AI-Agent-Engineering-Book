"""Unified chunking pipeline, comparison, and strategy registry."""

from __future__ import annotations

from typing import Callable

from chunkkit.fixed import chunk_fixed
from chunkkit.hierarchical import chunk_hierarchical
from chunkkit.recursive import chunk_recursive
from chunkkit.semantic import chunk_semantic
from chunkkit.sliding import chunk_sliding
from chunkkit.types import (
    ChunkReport,
    ChunkStrategy,
    CompareReport,
    SourceDocument,
)

ChunkFn = Callable[..., ChunkReport]

STRATEGIES: dict[str, ChunkFn] = {
    ChunkStrategy.FIXED.value: lambda doc, **kw: chunk_fixed(doc, **kw),
    ChunkStrategy.SLIDING.value: lambda doc, **kw: chunk_sliding(doc, **kw),
    ChunkStrategy.RECURSIVE.value: lambda doc, **kw: chunk_recursive(doc, **kw),
    ChunkStrategy.SEMANTIC.value: lambda doc, **kw: chunk_semantic(doc, **kw),
    ChunkStrategy.HIERARCHICAL.value: lambda doc, **kw: chunk_hierarchical(doc, **kw),
}


def chunk_document(
    doc: SourceDocument,
    strategy: str = "recursive",
    **kwargs: object,
) -> ChunkReport:
    key = strategy.lower()
    if key not in STRATEGIES:
        raise ValueError(f"unknown strategy {strategy!r}; choose from {sorted(STRATEGIES)}")
    fn = STRATEGIES[key]
    return fn(doc, **kwargs)  # type: ignore[misc]


def compare_strategies(
    doc: SourceDocument,
    strategies: list[str] | None = None,
    *,
    size: int = 400,
) -> CompareReport:
    strategies = strategies or [
        "fixed",
        "sliding",
        "recursive",
        "semantic",
        "hierarchical",
    ]
    out: dict[str, dict] = {}
    for name in strategies:
        kwargs: dict = {}
        if name == "fixed":
            kwargs = {"size": size, "overlap": size // 10}
        elif name == "sliding":
            kwargs = {"window": size, "stride": size // 2}
        elif name == "recursive":
            kwargs = {"chunk_size": size, "chunk_overlap": size // 10}
        elif name == "semantic":
            kwargs = {"max_chunk_chars": size + 100}
        elif name == "hierarchical":
            kwargs = {"parent_size": size * 2, "child_size": size // 2}
        rep = chunk_document(doc, name, **kwargs)
        out[name] = {
            "n_chunks": rep.n_chunks,
            "avg_chars": round(rep.avg_chars, 2),
            "avg_tokens_est": round(rep.avg_tokens_est, 2),
            "min_chars": rep.min_chars,
            "max_chars": rep.max_chars,
            "extras": rep.extras,
        }
    return CompareReport(doc_id=doc.id, strategies=out)
