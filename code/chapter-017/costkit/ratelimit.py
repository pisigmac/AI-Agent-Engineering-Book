"""Token-bucket rate limiter for QPS and token throughput."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable


class RateLimitExceeded(RuntimeError):
    def __init__(self, message: str, *, retry_after_s: float) -> None:
        super().__init__(message)
        self.retry_after_s = retry_after_s


@dataclass
class TokenBucket:
    capacity: float
    refill_per_s: float
    tokens: float
    updated_at: float

    def __init__(self, capacity: float, refill_per_s: float, *, now: float | None = None) -> None:
        if capacity <= 0 or refill_per_s < 0:
            raise ValueError("invalid bucket config")
        self.capacity = float(capacity)
        self.refill_per_s = float(refill_per_s)
        self.tokens = float(capacity)
        self.updated_at = now if now is not None else time.monotonic()

    def _refill(self, now: float) -> None:
        elapsed = max(0.0, now - self.updated_at)
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_s)
        self.updated_at = now

    def try_consume(self, amount: float = 1.0, *, now: float | None = None) -> float | None:
        """Return None if ok; else seconds until enough tokens."""
        now = time.monotonic() if now is None else now
        self._refill(now)
        if self.tokens >= amount:
            self.tokens -= amount
            return None
        need = amount - self.tokens
        if self.refill_per_s <= 0:
            return float("inf")
        return need / self.refill_per_s


class RateLimiter:
    """Combined request and token buckets (provider-style dual limits)."""

    def __init__(
        self,
        *,
        requests_per_minute: float = 60.0,
        tokens_per_minute: float = 100_000.0,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.clock = clock or time.monotonic
        rpm = max(requests_per_minute, 0.1)
        tpm = max(tokens_per_minute, 1.0)
        self.req_bucket = TokenBucket(rpm, rpm / 60.0, now=self.clock())
        self.tok_bucket = TokenBucket(tpm, tpm / 60.0, now=self.clock())

    def acquire(self, *, tokens: int = 0, requests: float = 1.0) -> None:
        now = self.clock()
        wait_req = self.req_bucket.try_consume(requests, now=now)
        wait_tok = self.tok_bucket.try_consume(float(max(tokens, 0)), now=now)
        waits = [w for w in (wait_req, wait_tok) if w is not None]
        if waits:
            retry = max(waits)
            raise RateLimitExceeded(
                f"rate limited; retry_after_s={retry:.3f}",
                retry_after_s=retry if retry != float("inf") else 60.0,
            )
