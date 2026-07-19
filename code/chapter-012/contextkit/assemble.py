"""Budgeted selection of context items."""

from __future__ import annotations

from contextkit.compress import compress_item
from contextkit.render import render_messages
from contextkit.tokens import TokenEstimator
from contextkit.types import (
    AssemblyReport,
    AssemblyResult,
    ContextItem,
    Kind,
    Priority,
    priority_rank,
)

# Within the same priority, prefer durable task signal over chatter/tools.
_KIND_RANK = {
    Kind.SYSTEM: 0,
    Kind.GOAL: 1,
    Kind.MEMORY: 2,
    Kind.TOOL: 3,
    Kind.HISTORY: 4,
}


class AssemblyError(RuntimeError):
    """Raised when a safe assembly cannot be produced."""


def _estimate_messages(items: list[ContextItem], estimator: TokenEstimator) -> int:
    messages = render_messages(items)
    return estimator.count_messages([m.to_dict() for m in messages])


def _sort_key_for_inclusion(item: ContextItem) -> tuple[int, int, int]:
    # Lower tuple sorts earlier: priority, kind usefulness, then newer first.
    return (
        priority_rank(item.priority),
        _KIND_RANK.get(item.kind, 9),
        -item.created_index,
    )


def select_items(
    items: list[ContextItem],
    estimator: TokenEstimator,
    *,
    budget: int,
    max_tokens_tool: int,
    max_tokens_memory: int,
) -> tuple[list[ContextItem], list[ContextItem], list[str], list[str]]:
    """Return (kept, dropped, compressed_ids, notes)."""
    if budget <= 0:
        raise AssemblyError("budget must be positive")

    notes: list[str] = []
    compressed_ids: list[str] = []
    working: list[ContextItem] = []
    for item in items:
        before = item.content
        compressed = compress_item(
            item,
            estimator,
            max_tokens_tool=max_tokens_tool,
            max_tokens_memory=max_tokens_memory,
        )
        if compressed.content != before:
            compressed_ids.append(compressed.item_id)
        if compressed.token_est is None:
            compressed.token_est = estimator.count_text(compressed.content)
        working.append(compressed)

    if compressed_ids:
        notes.append(f"compressed={len(compressed_ids)}")

    pinned = [i for i in working if i.priority is Priority.CRITICAL]
    flexible = [i for i in working if i.priority is not Priority.CRITICAL]

    pinned_tokens = _estimate_messages(pinned, estimator)
    if pinned_tokens > budget:
        raise AssemblyError(
            f"pinned policy/context alone estimates {pinned_tokens} tokens, "
            f"exceeding budget {budget}; refuse to call model without policy"
        )

    # Greedy add flexible items by importance then recency.
    flexible_sorted = sorted(flexible, key=_sort_key_for_inclusion)
    kept_flexible: list[ContextItem] = []
    dropped: list[ContextItem] = []

    for item in flexible_sorted:
        trial = pinned + _chronological(kept_flexible + [item])
        if _estimate_messages(trial, estimator) <= budget:
            kept_flexible.append(item)
        else:
            dropped.append(item)

    kept = pinned + _chronological(kept_flexible)

    # Final guard against estimator drift after render ordering.
    while kept and _estimate_messages(kept, estimator) > budget:
        # Drop worst flexible item still present.
        flex_ids = {i.item_id for i in kept if i.priority is not Priority.CRITICAL}
        if not flex_ids:
            break
        victim = max(
            (i for i in kept if i.item_id in flex_ids),
            key=lambda i: (priority_rank(i.priority), -i.created_index),
        )
        kept = [i for i in kept if i.item_id != victim.item_id]
        dropped.append(victim)
        notes.append(f"post_trim={victim.item_id}")

    dropped_ids = {d.item_id for d in dropped}
    # Ensure dropped list includes only items not kept
    kept_ids = {k.item_id for k in kept}
    dropped = [d for d in working if d.item_id not in kept_ids]
    if dropped_ids:
        notes.append(f"dropped={len(dropped)}")

    return kept, dropped, compressed_ids, notes


def _chronological(items: list[ContextItem]) -> list[ContextItem]:
    return sorted(items, key=lambda i: i.created_index)


def build_result(
    kept: list[ContextItem],
    dropped: list[ContextItem],
    *,
    budget: int,
    estimator: TokenEstimator,
    compressed_ids: list[str],
    notes: list[str],
    policy_id: str | None,
) -> AssemblyResult:
    messages = render_messages(kept)
    tokens_est = estimator.count_messages([m.to_dict() for m in messages])
    report = AssemblyReport(
        budget=budget,
        tokens_est=tokens_est,
        kept_ids=[i.item_id for i in kept],
        dropped_ids=[i.item_id for i in dropped],
        compressed_ids=list(compressed_ids),
        notes=list(notes),
        policy_id=policy_id,
    )
    return AssemblyResult(
        messages=messages,
        report=report,
        items_kept=kept,
        items_dropped=dropped,
    )
