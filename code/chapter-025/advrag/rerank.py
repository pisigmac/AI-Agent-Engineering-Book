"""Lightweight re-ranker (offline cross-encoder stand-in)."""

from __future__ import annotations

from advrag.tokenize import tokenize
from advrag.types import SearchHit


class SimpleReranker:
    """Score = α * dense_or_rrf_score + β * lexical_overlap + γ * title_hit."""

    def __init__(
        self,
        *,
        alpha: float = 0.55,
        beta: float = 0.35,
        gamma: float = 0.10,
    ) -> None:
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

    def rerank(self, query: str, hits: list[SearchHit], *, k: int | None = None) -> list[SearchHit]:
        if not hits:
            return []
        k = k or len(hits)
        q = set(tokenize(query))
        # normalize incoming scores to 0..1
        scores = [h.score for h in hits]
        lo, hi = min(scores), max(scores)
        span = (hi - lo) or 1.0

        rescored: list[SearchHit] = []
        for h in hits:
            norm = (h.score - lo) / span
            d_toks = set(tokenize(h.text))
            overlap = len(q & d_toks) / max(len(q), 1)
            title = str(h.metadata.get("title", "")).lower()
            title_hit = 1.0 if any(t in title for t in q) else 0.0
            final = self.alpha * norm + self.beta * overlap + self.gamma * title_hit
            rescored.append(
                SearchHit(
                    id=h.id,
                    text=h.text,
                    score=float(final),
                    metadata={**h.metadata, "pre_rerank_score": h.score},
                    parent_id=h.parent_id,
                    sources=h.sources + ("rerank",),
                    rank=0,
                )
            )
        rescored.sort(key=lambda x: (-x.score, x.id))
        out = []
        for i, h in enumerate(rescored[:k], start=1):
            out.append(
                SearchHit(
                    id=h.id,
                    text=h.text,
                    score=h.score,
                    metadata=h.metadata,
                    parent_id=h.parent_id,
                    sources=h.sources,
                    rank=i,
                )
            )
        return out
