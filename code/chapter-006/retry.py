"""Retry policy (async-friendly delays applied by the client)."""

from __future__ import annotations

import random
from dataclasses import dataclass

TRANSIENT = frozenset({408, 425, 429, 500, 502, 503, 504})


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_s: float = 0.05
    max_delay_s: float = 2.0
    jitter_s: float = 0.01

    def allow(
        self,
        method: str,
        status: int | None,
        idempotent: bool,
        attempt: int,
    ) -> bool:
        if attempt >= self.max_attempts:
            return False
        if status is None:
            return idempotent or method.upper() in {"GET", "HEAD", "OPTIONS"}
        if status == 429:
            return True
        if status in TRANSIENT:
            if method.upper() == "POST" and not idempotent:
                return False
            return idempotent or method.upper() in {
                "GET",
                "HEAD",
                "OPTIONS",
                "PUT",
                "DELETE",
            }
        return False

    def delay_s(self, attempt: int, retry_after_s: float | None = None) -> float:
        if retry_after_s is not None and retry_after_s >= 0:
            return min(self.max_delay_s, retry_after_s)
        exp = min(self.max_delay_s, self.base_delay_s * (2 ** max(0, attempt - 1)))
        return exp + random.uniform(0, self.jitter_s)
