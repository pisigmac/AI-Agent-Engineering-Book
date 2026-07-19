"""Async token-bucket rate limiter."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass


@dataclass
class AsyncTokenBucket:
    rate_per_s: float
    capacity: float
    tokens: float | None = None
    updated_at: float | None = None

    def __post_init__(self) -> None:
        if self.tokens is None:
            self.tokens = float(self.capacity)
        if self.updated_at is None:
            self.updated_at = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        assert self.updated_at is not None and self.tokens is not None
        elapsed = now - self.updated_at
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate_per_s)
        self.updated_at = now

    async def acquire(self, cost: float = 1.0) -> float:
        waited = 0.0
        while True:
            self._refill()
            assert self.tokens is not None
            if self.tokens >= cost:
                self.tokens -= cost
                return waited
            need = cost - self.tokens
            sleep_s = need / self.rate_per_s if self.rate_per_s > 0 else 0.05
            await asyncio.sleep(sleep_s)
            waited += sleep_s
