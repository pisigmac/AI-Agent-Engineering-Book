"""Payload compression with explicit truncation markers."""

from __future__ import annotations

from contextkit.tokens import TokenEstimator
from contextkit.types import ContextItem, Kind


def truncation_marker(original_chars: int) -> str:
    return f"\n\n[truncated: original_chars={original_chars}; content exceeded cap]"


def cap_text(text: str, estimator: TokenEstimator, *, max_tokens: int) -> tuple[str, bool]:
    """Return (possibly shortened text, truncated_flag)."""
    if max_tokens <= 0:
        return truncation_marker(len(text)).strip(), True
    if estimator.count_text(text) <= max_tokens:
        return text, False

    lo, hi = 0, len(text)
    best = 0
    while lo <= hi:
        mid = (lo + hi) // 2
        candidate = text[:mid] + truncation_marker(len(text))
        if estimator.count_text(candidate) <= max_tokens:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return text[:best] + truncation_marker(len(text)), True


def compress_item(
    item: ContextItem,
    estimator: TokenEstimator,
    *,
    max_tokens_tool: int,
    max_tokens_memory: int,
) -> ContextItem:
    """Cap bulky untrusted payloads; never auto-cap system policy items."""
    if item.kind is Kind.SYSTEM:
        return item

    limit: int | None
    if item.kind is Kind.TOOL:
        limit = max_tokens_tool
    elif item.kind is Kind.MEMORY:
        limit = max_tokens_memory
    else:
        limit = None

    if limit is None:
        item.token_est = estimator.count_text(item.content)
        return item

    new_content, truncated = cap_text(item.content, estimator, max_tokens=limit)
    meta = dict(item.metadata)
    if truncated:
        meta["truncated"] = True
        meta["original_chars"] = len(item.content)
    item.content = new_content
    item.metadata = meta
    item.token_est = estimator.count_text(item.content)
    return item
