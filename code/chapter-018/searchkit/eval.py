"""Retrieval evaluation: Recall@k, MRR, Precision@k."""

from __future__ import annotations

from searchkit.types import EvalReport, LabeledQuery, SearchHit


def recall_at_k(hits: list[SearchHit], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    top = {h.id for h in hits[:k]}
    return len(top & relevant) / len(relevant)


def precision_at_k(hits: list[SearchHit], relevant: set[str], k: int) -> float:
    if k <= 0:
        return 0.0
    top = hits[:k]
    if not top:
        return 0.0
    return sum(1 for h in top if h.id in relevant) / len(top)


def reciprocal_rank(hits: list[SearchHit], relevant: set[str]) -> float:
    for i, h in enumerate(hits, start=1):
        if h.id in relevant:
            return 1.0 / i
    return 0.0


def evaluate(
    labeled: list[LabeledQuery],
    search_fn,
    *,
    k: int = 3,
) -> EvalReport:
    """search_fn(query: str) -> list[SearchHit]."""
    recalls: list[float] = []
    precs: list[float] = []
    rrs: list[float] = []
    per: list[dict] = []
    for lq in labeled:
        hits = search_fn(lq.query)
        rel = set(lq.relevant_ids)
        r = recall_at_k(hits, rel, k)
        p = precision_at_k(hits, rel, k)
        rr = reciprocal_rank(hits, rel)
        recalls.append(r)
        precs.append(p)
        rrs.append(rr)
        per.append(
            {
                "query": lq.query,
                "relevant": list(lq.relevant_ids),
                "top_ids": [h.id for h in hits[:k]],
                "recall_at_k": round(r, 4),
                "precision_at_k": round(p, 4),
                "rr": round(rr, 4),
            }
        )
    n = len(labeled) or 1
    return EvalReport(
        n_queries=len(labeled),
        recall_at_k=sum(recalls) / n if labeled else 0.0,
        mrr=sum(rrs) / n if labeled else 0.0,
        precision_at_k=sum(precs) / n if labeled else 0.0,
        per_query=per,
    )
