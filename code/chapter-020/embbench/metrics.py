"""Vector math and retrieval metrics."""

from __future__ import annotations

import math
from typing import Sequence

Vector = Sequence[float]


def l2_normalize(v: Vector, *, eps: float = 1e-12) -> list[float]:
    n = math.sqrt(sum(x * x for x in v))
    if n < eps:
        return [0.0] * len(v)
    return [x / n for x in v]


def dot(a: Vector, b: Vector) -> float:
    if len(a) != len(b):
        raise ValueError(f"dim mismatch {len(a)} vs {len(b)}")
    return sum(x * y for x, y in zip(a, b))


def cosine(a: Vector, b: Vector) -> float:
    return dot(l2_normalize(a), l2_normalize(b))


def rank_documents(
    query_vec: list[float],
    doc_ids: list[str],
    doc_vecs: list[list[float]],
) -> list[tuple[str, float]]:
    scored = [(doc_ids[i], cosine(query_vec, doc_vecs[i])) for i in range(len(doc_ids))]
    scored.sort(key=lambda t: (-t[1], t[0]))
    return scored


def recall_at_k(ranked_ids: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    return len(set(ranked_ids[:k]) & relevant) / len(relevant)


def mrr(ranked_ids: list[str], relevant: set[str]) -> float:
    for i, doc_id in enumerate(ranked_ids, start=1):
        if doc_id in relevant:
            return 1.0 / i
    return 0.0
