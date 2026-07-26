"""Token estimation for chunk sizing (billing-grade counters in Ch 10)."""

from __future__ import annotations


def estimate_tokens(text: str) -> int:
    """Rough ~4 chars/token heuristic for planning chunk sizes."""
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def char_budget_for_tokens(token_budget: int) -> int:
    if token_budget < 1:
        raise ValueError("token_budget must be >= 1")
    return token_budget * 4
