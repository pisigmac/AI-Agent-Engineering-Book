"""Contextual compression: keep query-relevant sentences from hits."""

from __future__ import annotations

import re

from advrag.tokenize import tokenize
from advrag.types import SearchHit

_SENT = re.compile(r"(?<=[.!?])\s+|\n+")


def compress_hit(query: str, hit: SearchHit, *, max_chars: int = 280) -> SearchHit:
    """Extract sentences with highest token overlap to the query."""
    sents = [s.strip() for s in _SENT.split(hit.text) if s.strip()]
    if not sents:
        return hit
    q = set(tokenize(query))
    if not q:
        text = hit.text[:max_chars]
        return SearchHit(
            id=hit.id,
            text=text,
            score=hit.score,
            metadata={**hit.metadata, "compressed": True},
            parent_id=hit.parent_id,
            sources=hit.sources + ("compress",),
            rank=hit.rank,
        )

    ranked = sorted(
        sents,
        key=lambda s: len(q & set(tokenize(s))) / max(len(q), 1),
        reverse=True,
    )
    buf: list[str] = []
    total = 0
    for s in ranked:
        if total + len(s) + 1 > max_chars and buf:
            break
        buf.append(s)
        total += len(s) + 1
    # preserve rough reading order
    order = {s: i for i, s in enumerate(sents)}
    buf.sort(key=lambda s: order.get(s, 0))
    text = " ".join(buf)
    return SearchHit(
        id=hit.id,
        text=text,
        score=hit.score,
        metadata={**hit.metadata, "compressed": True, "orig_chars": len(hit.text)},
        parent_id=hit.parent_id,
        sources=hit.sources + ("compress",),
        rank=hit.rank,
    )


def compress_hits(query: str, hits: list[SearchHit], *, max_chars: int = 280) -> list[SearchHit]:
    return [compress_hit(query, h, max_chars=max_chars) for h in hits]
