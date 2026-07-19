"""Bounded parallel execution helpers."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Iterable, Sequence
from typing import TypeVar

from models import ItemResult

T = TypeVar("T")
R = TypeVar("R")


async def map_parallel(
    keys: Sequence[T],
    worker: Callable[[T], Awaitable[R]],
    *,
    concurrency: int = 5,
    key_fn: Callable[[T], str] | None = None,
) -> list[ItemResult]:
    """Run worker over keys with a concurrency cap; isolate per-item errors."""
    if concurrency < 1:
        raise ValueError("concurrency must be >= 1")
    sem = asyncio.Semaphore(concurrency)
    in_flight = 0
    max_in_flight = 0
    lock = asyncio.Lock()

    async def run_one(item: T) -> ItemResult:
        nonlocal in_flight, max_in_flight
        label = key_fn(item) if key_fn else str(item)
        async with sem:
            async with lock:
                in_flight += 1
                max_in_flight = max(max_in_flight, in_flight)
            try:
                value = await worker(item)
                return ItemResult(key=label, ok=True, value=value)
            except Exception as exc:  # noqa: BLE001 — isolate fan-out failures
                status = getattr(exc, "status_code", None)
                return ItemResult(
                    key=label,
                    ok=False,
                    error=str(exc),
                    status_code=status if isinstance(status, int) else None,
                )
            finally:
                async with lock:
                    in_flight -= 1

    results = await asyncio.gather(*(run_one(k) for k in keys))
    # Attach instrumentation for tests via function attribute
    map_parallel.last_max_in_flight = max_in_flight  # type: ignore[attr-defined]
    return list(results)


async def gather_limited(
    coros: Iterable[Awaitable[R]],
    *,
    concurrency: int = 5,
) -> list[R | BaseException]:
    """Like gather(return_exceptions=True) but with a concurrency cap."""
    sem = asyncio.Semaphore(concurrency)

    async def wrap(coro: Awaitable[R]) -> R | BaseException:
        async with sem:
            try:
                return await coro
            except BaseException as exc:  # noqa: BLE001
                return exc

    return list(await asyncio.gather(*(wrap(c) for c in coros)))


async def run_in_thread(fn: Callable[..., R], /, *args: object, **kwargs: object) -> R:
    """Offload blocking/CPU work so the event loop stays responsive."""
    return await asyncio.to_thread(fn, *args, **kwargs)
