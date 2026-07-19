"""Cross-cutting decorators: timing and retry."""

from __future__ import annotations

import functools
import time
from collections.abc import Callable
from typing import TypeVar

from pyutils.errors import TransientError

F = TypeVar("F", bound=Callable[..., object])


def timed(fn: F) -> F:
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            wrapper.last_elapsed_s = time.perf_counter() - start  # type: ignore[attr-defined]

    wrapper.last_elapsed_s = 0.0  # type: ignore[attr-defined]
    return wrapper  # type: ignore[return-value]


def retry(
    *,
    attempts: int = 3,
    exceptions: tuple[type[BaseException], ...] = (TransientError,),
    delay_s: float = 0.0,
) -> Callable[[F], F]:
    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last: BaseException | None = None
            for i in range(1, attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last = exc
                    if i >= attempts:
                        break
                    if delay_s > 0:
                        time.sleep(delay_s)
            assert last is not None
            raise last

        return wrapper  # type: ignore[return-value]

    return decorator
