"""Rank fusion utilities (RRF and weighted merge)."""

from __future__ import annotations

from collections import defaultdict

from advrag.types import SearchHit


def reciprocal_rank_fusion(
    hit_lists: list[list[SearchHit]],
    *,
    k: int = 10,
    rrf_k: int = 60,
) -> list[SearchHit]:
    """Fuse multiple ranked lists with Reciprocal Rank Fusion."""
    scores: dict[str, float] = defaultdict(float)
    best: dict[str, SearchHit] = {}
    sources: dict[str, set[str]] = defaultdict(set)

    for hits in hit_lists:
        for rank, hit in enumerate(hits, start=1):
            scores[hit.id] += 1.0 / (rrf_k + rank)
            sources[hit.id].update(hit.sources)
            prev = best.get(hit.id)
            if prev is None or hit.score > prev.score:
                best[hit.id] = hit

    ranked = sorted(scores.items(), key=lambda t: (-t[1], t[0]))[:k]
    out: list[SearchHit] = []
    for i, (doc_id, score) in enumerate(ranked, start=1):
        base = best[doc_id]
        out.append(
            SearchHit(
                id=base.id,
                text=base.text,
                score=float(score),
                metadata=dict(base.metadata),
                parent_id=base.parent_id,
                sources=tuple(sorted(sources[doc_id])),
                rank=i,
            )
        )
    return out
