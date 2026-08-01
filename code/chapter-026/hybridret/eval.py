"""Retrieval evaluation for hybrid experiments."""
from __future__ import annotations
from typing import Callable
from hybridret.types import EvalReport, Hit

def recall_at_k(hits: list[Hit], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    top = {h.id for h in hits[:k]}
    return len(top & relevant) / len(relevant)

def mrr(hits: list[Hit], relevant: set[str]) -> float:
    for i, h in enumerate(hits, 1):
        if h.id in relevant:
            return 1.0 / i
    return 0.0

def evaluate(search_fn: Callable[[str], list[Hit]], labels: list[tuple[str, tuple[str, ...]]], *, k: int = 3) -> EvalReport:
    recalls, rrs, rows = [], [], []
    for q, rel in labels:
        hits = search_fn(q)
        R = set(rel)
        r = recall_at_k(hits, R, k)
        rr = mrr(hits, R)
        recalls.append(r); rrs.append(rr)
        rows.append({"query": q, "relevant": list(rel), "top": [h.id for h in hits[:k]],
                     "recall_at_k": round(r, 4), "rr": round(rr, 4)})
    n = max(len(labels), 1)
    return EvalReport(len(labels), sum(recalls)/n if labels else 0.0, sum(rrs)/n if labels else 0.0, rows)
