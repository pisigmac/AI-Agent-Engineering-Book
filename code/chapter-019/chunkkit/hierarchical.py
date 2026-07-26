"""Hierarchical parent/child chunking for multi-granularity retrieval."""

from __future__ import annotations

from chunkkit.base import make_chunk, report_for
from chunkkit.fixed import chunk_fixed
from chunkkit.recursive import chunk_recursive
from chunkkit.types import Chunk, ChunkReport, SourceDocument


def chunk_hierarchical(
    doc: SourceDocument,
    *,
    parent_size: int = 800,
    child_size: int = 250,
    child_overlap: int = 40,
) -> ChunkReport:
    """Create parent chunks, then child chunks that reference parents.

    Parents are recursive mid-size sections; children are fixed windows for
    precise embedding match. Retrieval can return a child and expand to parent.
    """
    if parent_size <= child_size:
        raise ValueError("parent_size must be > child_size")

    parent_report = chunk_recursive(
        doc, chunk_size=parent_size, chunk_overlap=max(20, parent_size // 20)
    )
    # Re-tag parents as hierarchical level 0
    parents: list[Chunk] = []
    for i, p in enumerate(parent_report.chunks):
        parents.append(
            make_chunk(
                doc,
                p.text,
                p.start,
                p.end,
                strategy="hierarchical",
                index=i,
                parent_id=None,
                level=0,
                extra_meta={"role": "parent"},
            )
        )

    children: list[Chunk] = []
    child_idx = 0
    for parent in parents:
        # Chunk parent text with fixed strategy, map offsets into global doc
        pseudo = SourceDocument(
            id=parent.id,
            text=parent.text,
            metadata=doc.metadata,
            title=doc.title,
        )
        child_rep = chunk_fixed(pseudo, size=child_size, overlap=child_overlap)
        for ch in child_rep.chunks:
            # Map local offsets to parent global span
            g_start = parent.start + ch.start
            g_end = parent.start + ch.end
            # Clamp to parent
            g_end = min(g_end, parent.end)
            piece = doc.text[g_start:g_end] if g_start < len(doc.text) else ch.text
            children.append(
                make_chunk(
                    doc,
                    piece,
                    g_start,
                    g_end,
                    strategy="hierarchical",
                    index=child_idx,
                    parent_id=parent.id,
                    level=1,
                    extra_meta={"role": "child", "parent_title": doc.title},
                )
            )
            child_idx += 1

    all_chunks = parents + children
    return report_for(
        doc,
        "hierarchical",
        all_chunks,
        parent_size=parent_size,
        child_size=child_size,
        n_parents=len(parents),
        n_children=len(children),
    )


def expand_to_parent(chunk: Chunk, hierarchy: list[Chunk]) -> Chunk | None:
    """Given a child chunk, return its parent from a hierarchical report list."""
    if not chunk.parent_id:
        return None
    for c in hierarchy:
        if c.id == chunk.parent_id:
            return c
    return None
