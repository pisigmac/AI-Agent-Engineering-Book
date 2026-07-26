"""Cost dashboard aggregation and optimization hints."""

from __future__ import annotations

from collections import defaultdict

from costkit.types import CacheOutcome, DashboardSnapshot, UsageEvent


def build_dashboard(events: list[UsageEvent]) -> DashboardSnapshot:
    total_cost = 0.0
    total_in = 0
    total_out = 0
    lat_sum = 0.0
    hits = 0
    misses = 0
    saved = 0.0
    cost_by: dict[str, float] = defaultdict(float)
    calls_by: dict[str, int] = defaultdict(int)

    for e in events:
        total_cost += e.cost_usd
        total_in += e.usage.input_tokens
        total_out += e.usage.output_tokens
        lat_sum += e.latency_ms
        calls_by[e.model_id] += 1
        cost_by[e.model_id] += e.cost_usd
        if e.cache is CacheOutcome.HIT:
            hits += 1
            saved += float(e.metadata.get("saved_cost_usd", 0.0))
        elif e.cache is CacheOutcome.MISS:
            misses += 1

    n = len(events)
    avg_lat = (lat_sum / n) if n else 0.0
    recs = _recommendations(
        events,
        total_cost=total_cost,
        hits=hits,
        misses=misses,
        cost_by=dict(cost_by),
    )
    return DashboardSnapshot(
        total_cost_usd=total_cost,
        total_calls=n,
        cache_hits=hits,
        cache_misses=misses,
        total_input_tokens=total_in,
        total_output_tokens=total_out,
        avg_latency_ms=avg_lat,
        cost_by_model=dict(sorted(cost_by.items(), key=lambda kv: -kv[1])),
        calls_by_model=dict(sorted(calls_by.items(), key=lambda kv: -kv[1])),
        saved_cost_usd_estimate=saved,
        recommendations=recs,
    )


def _recommendations(
    events: list[UsageEvent],
    *,
    total_cost: float,
    hits: int,
    misses: int,
    cost_by: dict[str, float],
) -> list[str]:
    recs: list[str] = []
    total_cm = hits + misses
    if total_cm >= 5 and hits / total_cm < 0.1:
        recs.append("Low cache hit rate — enable exact cache for idempotent prompts (temperature=0).")
    if cost_by:
        top_model, top_cost = next(iter(sorted(cost_by.items(), key=lambda kv: -kv[1])))
        if total_cost > 0 and top_cost / total_cost > 0.6:
            recs.append(
                f"Model {top_model} is {top_cost / total_cost:.0%} of spend — "
                "route easy traffic to a cheaper SKU (Ch 16)."
            )
    # High output ratio may mean verbose completions
    tin = sum(e.usage.input_tokens for e in events) or 1
    tout = sum(e.usage.output_tokens for e in events)
    if tout / tin > 2.0 and tout > 2000:
        recs.append("Output tokens dominate — cap max_tokens and tighten prompts.")
    slow = [e for e in events if e.latency_ms >= 500]
    if len(events) >= 5 and len(slow) / len(events) > 0.4:
        recs.append("Many slow calls — prefer faster models or smaller prompts.")
    if not recs:
        recs.append("No urgent issues detected in this window.")
    return recs
