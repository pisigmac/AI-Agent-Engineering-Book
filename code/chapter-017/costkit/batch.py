"""Request batching for embed/classify style workloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Generic, Sequence, TypeVar

T = TypeVar("T")
R = TypeVar("R")


@dataclass
class BatchStats:
    batches: int = 0
    items: int = 0
    # Items that would have been 1-by-1 calls
    calls_saved: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "batches": self.batches,
            "items": self.items,
            "calls_saved": self.calls_saved,
        }


@dataclass
class Batcher(Generic[T, R]):
    """Accumulate items and flush in chunks through a batch function."""

    batch_fn: Callable[[Sequence[T]], list[R]]
    max_size: int = 32
    _buffer: list[T] = field(default_factory=list)
    stats: BatchStats = field(default_factory=BatchStats)

    def __post_init__(self) -> None:
        if self.max_size < 1:
            raise ValueError("max_size must be >= 1")

    def add(self, item: T) -> list[R]:
        self._buffer.append(item)
        if len(self._buffer) >= self.max_size:
            return self.flush()
        return []

    def add_many(self, items: Sequence[T]) -> list[R]:
        out: list[R] = []
        for it in items:
            out.extend(self.add(it))
        return out

    def flush(self) -> list[R]:
        if not self._buffer:
            return []
        chunk = self._buffer
        self._buffer = []
        results = self.batch_fn(chunk)
        if len(results) != len(chunk):
            raise RuntimeError(
                f"batch_fn returned {len(results)} results for {len(chunk)} items"
            )
        self.stats.batches += 1
        self.stats.items += len(chunk)
        self.stats.calls_saved += max(0, len(chunk) - 1)
        return results

    def map_all(self, items: Sequence[T]) -> list[R]:
        out = self.add_many(items)
        out.extend(self.flush())
        return out
