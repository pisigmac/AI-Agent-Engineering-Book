"""Iterator helpers for batching and streaming-style pipelines."""

from __future__ import annotations

from typing import Iterable, Iterator, TypeVar

T = TypeVar("T")


def batched(items: Iterable[T], size: int) -> Iterator[list[T]]:
    if size <= 0:
        raise ValueError("size must be positive")
    batch: list[T] = []
    for item in items:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def first_n(items: Iterable[T], n: int) -> list[T]:
    if n < 0:
        raise ValueError("n must be >= 0")
    out: list[T] = []
    for i, item in enumerate(items):
        if i >= n:
            break
        out.append(item)
    return out


def sliding_window(items: list[T], size: int) -> Iterator[list[T]]:
    if size <= 0:
        raise ValueError("size must be positive")
    if size > len(items):
        if items:
            yield list(items)
        return
    for i in range(0, len(items) - size + 1):
        yield items[i : i + size]
