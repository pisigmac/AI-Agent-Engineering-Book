"""Pure policy helpers (unit-testable, no I/O)."""

from __future__ import annotations

from dataclasses import dataclass


TRANSIENT_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})


@dataclass(frozen=True)
class RetryDecision:
    retry: bool
    reason: str


def should_retry(
    *,
    method: str,
    status_code: int | None,
    idempotent: bool,
    attempt: int,
    max_attempts: int = 3,
) -> RetryDecision:
    """Decide whether another HTTP attempt is appropriate.

    Mirrors Chapter 5 lessons in pure form for reuse in adapters.
    """
    if attempt >= max_attempts:
        return RetryDecision(False, "max_attempts_reached")
    if status_code is None:
        if idempotent or method.upper() in {"GET", "HEAD", "OPTIONS"}:
            return RetryDecision(True, "network_error_on_safe_or_idempotent")
        return RetryDecision(False, "network_error_on_unsafe_non_idempotent")
    if status_code == 429:
        return RetryDecision(True, "rate_limited")
    if status_code in TRANSIENT_STATUS:
        if method.upper() == "POST" and not idempotent:
            return RetryDecision(False, "transient_on_non_idempotent_post")
        if idempotent or method.upper() in {"GET", "HEAD", "OPTIONS", "PUT", "DELETE"}:
            return RetryDecision(True, "transient_status")
        return RetryDecision(False, "transient_but_unsafe_method")
    return RetryDecision(False, "non_retryable_status")
