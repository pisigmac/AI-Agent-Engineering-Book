"""Bounded retries with exponential backoff (cost-aware)."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    base_delay_s: float = 0.05
    max_delay_s: float = 2.0
    jitter: float = 0.1
    retry_on: tuple[type[BaseException], ...] = (TimeoutError, ConnectionError, RuntimeError)

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")


@dataclass
class RetryReport:
    attempts: int
    delays_s: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "attempts": self.attempts,
            "delays_s": self.delays_s,
            "errors": self.errors,
        }


def run_with_retry(
    fn: Callable[[], T],
    policy: RetryPolicy | None = None,
    *,
    sleep: Callable[[float], None] | None = None,
    rng: random.Random | None = None,
) -> tuple[T, RetryReport]:
    """Execute fn with retries. sleep injectable for tests (default time.sleep)."""
    policy = policy or RetryPolicy()
    sleep = sleep or time.sleep
    rng = rng or random.Random(0)
    report = RetryReport(attempts=0)
    last: BaseException | None = None

    for attempt in range(1, policy.max_attempts + 1):
        report.attempts = attempt
        try:
            return fn(), report
        except policy.retry_on as exc:  # type: ignore[misc]
            last = exc
            report.errors.append(f"{type(exc).__name__}: {exc}")
            if attempt >= policy.max_attempts:
                break
            delay = min(
                policy.max_delay_s,
                policy.base_delay_s * (2 ** (attempt - 1)),
            )
            delay *= 1.0 + rng.uniform(-policy.jitter, policy.jitter)
            delay = max(0.0, delay)
            report.delays_s.append(delay)
            sleep(delay)
        except BaseException:
            raise

    assert last is not None
    raise last
