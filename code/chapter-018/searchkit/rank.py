"""Post-retrieval ranking: boosts, MMR diversity, score normalization."""

from __future__ import annotations

from searchkit.metrics import cosine_similarity
from searchkit.types import SearchHit, VectorRecord


def minmax_normalize(hits: list[SearchHit]) -> list[SearchHit]:
    if not hits:
        return hits
    scores = [h.score for h in hits]
    lo, hi = min(scores), max(scores)
    if hi - lo < 1e-12:
        return [
            SearchHit(
                id=h.id,
                score=1.0,
                text=h.text,
                metadata=h.metadata,
                title=h.title,
                rank=h.rank,
                score_components={**h.score_components, "normalized": 1.0},
            )
            for h in hits
        ]
    out: list[SearchHit] = []
    for h in hits:
        n = (h.score - lo) / (hi - lo)
        out.append(
            SearchHit(
                id=h.id,
                score=n,
                text=h.text,
                metadata=h.metadata,
                title=h.title,
                rank=h.rank,
                score_components={**h.score_components, "raw": h.score, "normalized": n},
            )
        )
    return out


def apply_metadata_boosts(
    hits: list[SearchHit],
    *,
    boosts: dict[str, dict[object, float]] | None = None,
    title_substr_boost: tuple[str, float] | None = None,
) -> list[SearchHit]:
    """Multiply score by per-metadata boosts (e.g. topic=billing → 1.15)."""
    boosts = boosts or {}
    out: list[SearchHit] = []
    for h in hits:
        mult = 1.0
        components = dict(h.score_components)
        for key, value_map in boosts.items():
            val = h.metadata.get(key)
            if val in value_map:
                mult *= value_map[val]
                components[f"boost_{key}"] = value_map[val]
        if title_substr_boost:
            needle, b = title_substr_boost
            if needle.lower() in (h.title or "").lower() or needle.lower() in h.text.lower():
                mult *= b
                components["boost_title"] = b
        new_score = h.score * mult
        components["boosted"] = new_score
        out.append(
            SearchHit(
                id=h.id,
                score=new_score,
                text=h.text,
                metadata=h.metadata,
                title=h.title,
                rank=h.rank,
                score_components=components,
            )
        )
    out.sort(key=lambda x: (-x.score, x.id))
    return [
        SearchHit(
            id=h.id,
            score=h.score,
            text=h.text,
            metadata=h.metadata,
            title=h.title,
            rank=i,
            score_components=h.score_components,
        )
        for i, h in enumerate(out, start=1)
    ]


def mmr_rerank(
    hits: list[SearchHit],
    records_by_id: dict[str, VectorRecord],
    query_vector: list[float],
    *,
    lambda_mult: float = 0.7,
    k: int | None = None,
) -> list[SearchHit]:
    """Maximal Marginal Relevance: balance relevance vs diversity.

    score = λ * sim(q, d) - (1-λ) * max sim(d, selected)
    """
    if not hits:
        return []
    k = k or len(hits)
    lambda_mult = min(1.0, max(0.0, lambda_mult))
    candidates = {h.id: h for h in hits}
    selected: list[str] = []
    remaining = set(candidates.keys())

    while remaining and len(selected) < k:
        best_id = None
        best_score = float("-inf")
        best_comp: dict[str, float] = {}
        for doc_id in remaining:
            rec = records_by_id.get(doc_id)
            base = candidates[doc_id]
            if rec is None:
                rel = base.score
                div = 0.0
            else:
                rel = cosine_similarity(query_vector, rec.vector)
                if selected:
                    div = max(
                        cosine_similarity(rec.vector, records_by_id[s].vector)
                        for s in selected
                        if s in records_by_id
                    )
                else:
                    div = 0.0
            mmr = lambda_mult * rel - (1.0 - lambda_mult) * div
            if mmr > best_score:
                best_score = mmr
                best_id = doc_id
                best_comp = {
                    "relevance": rel,
                    "diversity_penalty": div,
                    "mmr": mmr,
                    "lambda": lambda_mult,
                }
        assert best_id is not None
        selected.append(best_id)
        remaining.remove(best_id)
        # stash components on a mutable path via candidates rebuild later
        candidates[best_id] = SearchHit(
            id=best_id,
            score=best_score,
            text=candidates[best_id].text,
            metadata=candidates[best_id].metadata,
            title=candidates[best_id].title,
            rank=0,
            score_components={**candidates[best_id].score_components, **best_comp},
        )

    out: list[SearchHit] = []
    for i, doc_id in enumerate(selected, start=1):
        h = candidates[doc_id]
        out.append(
            SearchHit(
                id=h.id,
                score=h.score,
                text=h.text,
                metadata=h.metadata,
                title=h.title,
                rank=i,
                score_components=h.score_components,
            )
        )
    return out
