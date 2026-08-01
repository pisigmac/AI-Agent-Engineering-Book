"""Score fusion: RRF and weighted normalized fusion."""
from __future__ import annotations
from collections import defaultdict
from hybridret.types import Hit

def rrf(lists: list[list[Hit]], *, k: int = 10, rrf_k: int = 60) -> list[Hit]:
    scores: dict[str, float] = defaultdict(float)
    best: dict[str, Hit] = {}
    channels: dict[str, set[str]] = defaultdict(set)
    for hits in lists:
        for rank, h in enumerate(hits, 1):
            scores[h.id] += 1.0 / (rrf_k + rank)
            channels[h.id].add(h.channel)
            if h.id not in best or h.score > best[h.id].score:
                best[h.id] = h
    ranked = sorted(scores.items(), key=lambda t: (-t[1], t[0]))[:k]
    out = []
    for i, (doc_id, sc) in enumerate(ranked, 1):
        h = best[doc_id]
        out.append(Hit(h.id, float(sc), h.text, dict(h.metadata),
                       "+".join(sorted(channels[doc_id])) or "rrf", i))
    return out

def weighted_fuse(lists: list[list[Hit]], weights: list[float], *, k: int = 10) -> list[Hit]:
    if len(lists) != len(weights):
        raise ValueError("weights length must match lists")
    scores: dict[str, float] = defaultdict(float)
    best: dict[str, Hit] = {}
    channels: dict[str, set[str]] = defaultdict(set)
    for hits, w in zip(lists, weights):
        if not hits:
            continue
        vals = [h.score for h in hits]
        lo, hi = min(vals), max(vals)
        span = (hi - lo) or 1.0
        for h in hits:
            norm = (h.score - lo) / span
            scores[h.id] += w * norm
            channels[h.id].add(h.channel)
            if h.id not in best or h.score > best[h.id].score:
                best[h.id] = h
    ranked = sorted(scores.items(), key=lambda t: (-t[1], t[0]))[:k]
    return [Hit(best[i].id, float(s), best[i].text, dict(best[i].metadata),
                "+".join(sorted(channels[i])) or "weighted", r)
            for r, (i, s) in enumerate(ranked, 1)]
