"""Shared chunk construction helpers."""

from __future__ import annotations

from chunkkit.tokens import estimate_tokens
from chunkkit.types import Chunk, ChunkReport, SourceDocument


def make_chunk(
    doc: SourceDocument,
    text: str,
    start: int,
    end: int,
    *,
    strategy: str,
    index: int,
    parent_id: str | None = None,
    level: int = 0,
    extra_meta: dict | None = None,
) -> Chunk:
    meta = dict(doc.metadata)
    if extra_meta:
        meta.update(extra_meta)
    meta.setdefault("title", doc.title)
    body = text
    # Prefer hierarchical ids when level/parent set
    if parent_id is not None or level > 0:
        cid = f"{doc.id}::L{level}::c{index:04d}"
    else:
        cid = f"{doc.id}::c{index:04d}"
    return Chunk(
        id=cid,
        doc_id=doc.id,
        text=body,
        start=start,
        end=end,
        strategy=strategy,
        index=index,
        parent_id=parent_id,
        level=level,
        metadata=meta,
        token_estimate=estimate_tokens(body),
    )


def report_for(
    doc: SourceDocument, strategy: str, chunks: list[Chunk], **extras: object
) -> ChunkReport:
    if not chunks:
        return ChunkReport(
            doc_id=doc.id,
            strategy=strategy,
            n_chunks=0,
            avg_chars=0.0,
            avg_tokens_est=0.0,
            min_chars=0,
            max_chars=0,
            chunks=[],
            extras=dict(extras),
        )
    lengths = [len(c.text) for c in chunks]
    toks = [c.token_estimate for c in chunks]
    return ChunkReport(
        doc_id=doc.id,
        strategy=strategy,
        n_chunks=len(chunks),
        avg_chars=sum(lengths) / len(lengths),
        avg_tokens_est=sum(toks) / len(toks),
        min_chars=min(lengths),
        max_chars=max(lengths),
        chunks=chunks,
        extras=dict(extras),
    )


def find_span(full: str, piece: str, *, from_idx: int = 0) -> tuple[int, int]:
    """Locate piece in full text; fallback to synthetic offsets."""
    if not piece:
        return from_idx, from_idx
    pos = full.find(piece, from_idx)
    if pos < 0:
        pos = full.find(piece)
    if pos < 0:
        return from_idx, from_idx + len(piece)
    return pos, pos + len(piece)
