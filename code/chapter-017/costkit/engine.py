"""Cost-aware completion engine: rate limit, cache, budget, retries, ledger."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Callable

from costkit.budget import BudgetExceeded, BudgetTracker
from costkit.cache import ResponseCache, make_cache_key
from costkit.compress import compress_text, estimate_tokens
from costkit.dashboard import build_dashboard
from costkit.pricing import PriceBook
from costkit.ratelimit import RateLimitExceeded, RateLimiter
from costkit.retry import RetryPolicy, run_with_retry
from costkit.types import (
    Budget,
    CacheOutcome,
    CallKind,
    DashboardSnapshot,
    TokenUsage,
    UsageEvent,
)


@dataclass
class CompleteRequest:
    prompt: str
    model_id: str = "mock-default"
    system: str = ""
    temperature: float = 0.0
    use_cache: bool = True
    compress: bool = False
    max_prompt_chars: int | None = None
    kind: CallKind = CallKind.CHAT


@dataclass
class CompleteResponse:
    text: str
    event: UsageEvent
    from_cache: bool

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "from_cache": self.from_cache,
            "event": self.event.to_dict(),
        }


@dataclass
class MockModel:
    """Deterministic offline model with optional flaky failures."""

    fail_times: int = 0
    _failures_left: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        self._failures_left = self.fail_times

    def complete(self, model_id: str, prompt: str, system: str = "") -> tuple[str, TokenUsage, float]:
        if self._failures_left > 0:
            self._failures_left -= 1
            raise TimeoutError("simulated transient timeout")
        text = f"[{model_id}] {prompt[:180]}"
        usage = TokenUsage(
            input_tokens=estimate_tokens(system + prompt),
            output_tokens=estimate_tokens(text),
        )
        latency_ms = 25.0 + usage.total * 0.01
        return text, usage, latency_ms


@dataclass
class CostEngine:
    """Production-shaped control plane for cost & performance demos."""

    prices: PriceBook = field(default_factory=PriceBook)
    cache: ResponseCache = field(default_factory=lambda: ResponseCache(ttl_s=600))
    limiter: RateLimiter = field(
        default_factory=lambda: RateLimiter(requests_per_minute=120, tokens_per_minute=200_000)
    )
    budget: BudgetTracker | None = None
    model: MockModel = field(default_factory=MockModel)
    retry: RetryPolicy = field(default_factory=lambda: RetryPolicy(max_attempts=3, base_delay_s=0.0))
    ledger: list[UsageEvent] = field(default_factory=list)
    sleep: Callable[[float], None] = field(default=lambda _s: None)

    def set_budget(self, budget: Budget) -> None:
        self.budget = BudgetTracker(budget)

    def complete(self, req: CompleteRequest) -> CompleteResponse:
        prompt = req.prompt
        if req.compress:
            prompt = compress_text(prompt, max_chars=req.max_prompt_chars).compressed
        elif req.max_prompt_chars is not None:
            prompt = compress_text(prompt, max_chars=req.max_prompt_chars).compressed

        key = make_cache_key(
            model_id=req.model_id,
            prompt=prompt,
            system=req.system,
            temperature=req.temperature,
        )

        if req.use_cache and req.temperature == 0.0:
            cached = self.cache.get(key)
            if cached is not None:
                text, usage, latency_ms, unit_cost = cached
                event = UsageEvent(
                    model_id=req.model_id,
                    usage=TokenUsage(0, 0),  # not re-billed
                    cost_usd=0.0,
                    latency_ms=latency_ms * 0.05,
                    kind=req.kind,
                    cache=CacheOutcome.HIT,
                    request_id=str(uuid.uuid4()),
                    metadata={"saved_cost_usd": unit_cost, "prompt_tokens_est": usage.input_tokens},
                )
                self.ledger.append(event)
                if self.budget:
                    # cache hits: record call with zero cost
                    try:
                        self.budget.record(event)
                    except BudgetExceeded:
                        # still append ledger; re-raise
                        raise
                return CompleteResponse(text=text, event=event, from_cache=True)
        else:
            if not req.use_cache:
                self.cache.bypass()

        # Estimate for rate limit + budget reservation
        est_in = estimate_tokens(req.system + prompt)
        est_out = 64
        est_usage = TokenUsage(est_in, est_out)
        est_cost = self.prices.cost(req.model_id, est_usage)
        if self.budget:
            self.budget.reserve_or_raise(cost_usd=est_cost, usage=est_usage)

        try:
            self.limiter.acquire(tokens=est_in + est_out, requests=1.0)
        except RateLimitExceeded:
            raise

        def _call() -> tuple[str, TokenUsage, float]:
            return self.model.complete(req.model_id, prompt, req.system)

        (text, usage, latency_ms), _report = run_with_retry(
            _call, self.retry, sleep=self.sleep
        )
        cost = self.prices.cost(req.model_id, usage)
        event = UsageEvent(
            model_id=req.model_id,
            usage=usage,
            cost_usd=cost,
            latency_ms=latency_ms,
            kind=req.kind,
            cache=CacheOutcome.MISS,
            request_id=str(uuid.uuid4()),
            metadata={"retries": _report.attempts},
        )

        if req.use_cache and req.temperature == 0.0:
            self.cache.set(key, (text, usage, latency_ms, cost), model_id=req.model_id, unit_cost_usd=cost)

        self.ledger.append(event)
        if self.budget:
            # Adjust: we reserved estimate; record actual (simple model: just record actual)
            # Revert estimate reservation by tracking actual only — BudgetTracker records actuals.
            # We already reserved via would_exceed check; record uses actuals.
            # Manually fix: BudgetTracker.record adds actuals; reservation only checked.
            self.budget.record(event)
        return CompleteResponse(text=text, event=event, from_cache=False)

    def dashboard(self) -> DashboardSnapshot:
        return build_dashboard(self.ledger)
