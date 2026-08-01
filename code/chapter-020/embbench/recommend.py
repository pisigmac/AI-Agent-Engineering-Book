"""Decision helper for embedding model selection."""

from __future__ import annotations

from embbench.catalog import catalog_by_id
from embbench.types import EmbeddingModelCard


def recommend(
    *,
    multilingual: bool = False,
    prefer_local: bool = False,
    max_cost_per_1m: float | None = None,
    max_dimensions: int | None = None,
    need_instructions: bool = False,
) -> dict:
    cards = list(catalog_by_id().values())
    # Prefer real catalog entries over pure teaching when recommending for prod
    candidates: list[EmbeddingModelCard] = []
    for c in cards:
        if c.provider.value == "teaching":
            continue
        if multilingual and not c.multilingual:
            continue
        if prefer_local and c.family.value != "open_weights":
            continue
        if max_cost_per_1m is not None and c.cost_per_1m_tokens > max_cost_per_1m:
            continue
        if max_dimensions is not None and c.dimensions > max_dimensions:
            continue
        if need_instructions and not c.supports_instructions:
            continue
        candidates.append(c)

    if not candidates:
        # fall back to teaching
        candidates = [catalog_by_id()["teaching:char-ngram"]]

    # Score: multilingual match, lower cost, moderate dims, instruction support
    def score(c: EmbeddingModelCard) -> float:
        s = 0.0
        if multilingual and c.multilingual:
            s += 2.0
        if prefer_local and c.cost_per_1m_tokens == 0:
            s += 1.5
        s += 1.0 / (1.0 + c.cost_per_1m_tokens)
        # prefer not huge dims for storage unless quality needed
        s += 1.0 / (1.0 + c.dimensions / 1024.0)
        if need_instructions and c.supports_instructions:
            s += 0.5
        if c.latency_class == "fast":
            s += 0.25
        return s

    ranked = sorted(candidates, key=lambda c: (-score(c), c.model_id))
    top = ranked[0]
    return {
        "recommended": top.model_id,
        "display_name": top.display_name,
        "score": round(score(top), 4),
        "constraints": {
            "multilingual": multilingual,
            "prefer_local": prefer_local,
            "max_cost_per_1m": max_cost_per_1m,
            "max_dimensions": max_dimensions,
            "need_instructions": need_instructions,
        },
        "alternatives": [c.model_id for c in ranked[1:4]],
        "card": top.to_dict(),
        "caveat": "Validate with embbench on your labeled queries before pinning.",
    }
