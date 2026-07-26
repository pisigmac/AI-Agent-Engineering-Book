"""Tests for cost & performance control plane."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from costkit.batch import Batcher
from costkit.budget import BudgetExceeded, BudgetTracker
from costkit.cache import ResponseCache, make_cache_key
from costkit.compress import compress_text, estimate_tokens
from costkit.dashboard import build_dashboard
from costkit.engine import CompleteRequest, CostEngine, MockModel
from costkit.pricing import PriceBook
from costkit.ratelimit import RateLimitExceeded, RateLimiter, TokenBucket
from costkit.retry import RetryPolicy, run_with_retry
from costkit.stream import consume_stream, iter_mock_stream
from costkit.types import Budget, CacheOutcome, CallKind, TokenUsage, UsageEvent


def test_pricing_cost():
    book = PriceBook()
    usage = TokenUsage(1_000_000, 1_000_000)
    c = book.cost("openai:gpt-balanced", usage)
    assert abs(c - (2.50 + 10.00)) < 1e-9


def test_cache_hit_saves_cost():
    engine = CostEngine()
    req = CompleteRequest(prompt="hello cache", model_id="mock-default", use_cache=True)
    r1 = engine.complete(req)
    r2 = engine.complete(req)
    assert not r1.from_cache and r1.event.cost_usd > 0
    assert r2.from_cache and r2.event.cost_usd == 0.0
    assert r2.event.cache is CacheOutcome.HIT
    dash = engine.dashboard()
    assert dash.cache_hits == 1
    assert dash.saved_cost_usd_estimate > 0


def test_budget_blocks_overspend():
    engine = CostEngine()
    engine.set_budget(Budget(max_cost_usd=0.0000001, max_calls=10))
    with pytest.raises(BudgetExceeded):
        engine.complete(
            CompleteRequest(
                prompt="x" * 4000,
                model_id="openai:gpt-flagship",
                use_cache=False,
                temperature=0.5,
            )
        )


def test_budget_max_calls():
    engine = CostEngine()
    engine.set_budget(Budget(max_calls=2))
    engine.complete(CompleteRequest(prompt="a", model_id="google:gemini-flash"))
    engine.complete(CompleteRequest(prompt="b", model_id="google:gemini-flash"))
    with pytest.raises(BudgetExceeded):
        engine.complete(CompleteRequest(prompt="c", model_id="google:gemini-flash"))


def test_rate_limiter():
    lim = RateLimiter(requests_per_minute=2, tokens_per_minute=10_000)
    lim.acquire(tokens=1)
    lim.acquire(tokens=1)
    with pytest.raises(RateLimitExceeded) as exc:
        lim.acquire(tokens=1)
    assert exc.value.retry_after_s > 0


def test_token_bucket_refill():
    b = TokenBucket(capacity=2, refill_per_s=1000.0, now=0.0)
    assert b.try_consume(1, now=0.0) is None
    assert b.try_consume(1, now=0.0) is None
    wait = b.try_consume(1, now=0.0)
    assert wait is not None and wait > 0
    assert b.try_consume(1, now=1.0) is None


def test_retry_succeeds_after_failures():
    state = {"n": 0}

    def flaky() -> str:
        state["n"] += 1
        if state["n"] < 3:
            raise TimeoutError("nope")
        return "ok"

    val, report = run_with_retry(
        flaky,
        RetryPolicy(max_attempts=3, base_delay_s=0.0, jitter=0.0),
        sleep=lambda _s: None,
    )
    assert val == "ok"
    assert report.attempts == 3


def test_retry_exhausted():
    def always() -> None:
        raise ConnectionError("down")

    with pytest.raises(ConnectionError):
        run_with_retry(
            always,
            RetryPolicy(max_attempts=2, base_delay_s=0.0, jitter=0.0),
            sleep=lambda _s: None,
        )


def test_engine_retries_transient():
    engine = CostEngine(model=MockModel(fail_times=2), retry=RetryPolicy(max_attempts=3, base_delay_s=0.0, jitter=0.0))
    r = engine.complete(CompleteRequest(prompt="retry me", model_id="mistral:small", use_cache=False, temperature=0.2))
    assert r.text
    assert r.event.metadata.get("retries") == 3


def test_batcher():
    def fn(items: list[int]) -> list[int]:
        return [x * 2 for x in items]

    b = Batcher(fn, max_size=2)
    out = b.map_all([1, 2, 3])
    assert out == [2, 4, 6]
    assert b.stats.batches == 2
    assert b.stats.calls_saved == 1  # one batch of 2 saves 1; batch of 1 saves 0


def test_compress_reduces_size():
    text = "Hello,   world.\n\n\n\nThis   is   spaced."
    r = compress_text(text)
    assert r.compressed_chars <= r.original_chars
    assert "  " not in r.compressed


def test_stream_accumulator():
    chunks = list(iter_mock_stream("abcdefghij", chunk_chars=3))
    acc = consume_stream(chunks, model_id="m", input_tokens=5)
    text, tin, tout = acc.finalize()
    assert text == "abcdefghij"
    assert tin == 5
    assert tout > 0
    assert acc.chunks >= 3


def test_dashboard_recommendations_low_cache():
    events = [
        UsageEvent(
            model_id="openai:gpt-flagship",
            usage=TokenUsage(100, 200),
            cost_usd=0.05,
            latency_ms=600,
            cache=CacheOutcome.MISS,
        )
        for _ in range(6)
    ]
    dash = build_dashboard(events)
    assert dash.total_calls == 6
    assert any("cache" in r.lower() or "flagship" in r.lower() or "slow" in r.lower() for r in dash.recommendations)


def test_make_cache_key_stable():
    a = make_cache_key(model_id="m", prompt="p", system="s", temperature=0.0)
    b = make_cache_key(model_id="m", prompt="p", system="s", temperature=0.0)
    c = make_cache_key(model_id="m", prompt="p2", system="s", temperature=0.0)
    assert a == b and a != c


def test_estimate_tokens():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1


def test_budget_tracker_status():
    t = BudgetTracker(Budget(max_cost_usd=1.0, max_calls=5))
    t.record(
        UsageEvent(
            model_id="m",
            usage=TokenUsage(10, 10),
            cost_usd=0.5,
            latency_ms=10,
            kind=CallKind.CHAT,
        )
    )
    st = t.status()
    assert st.ok and st.calls == 1
