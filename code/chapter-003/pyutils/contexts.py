"""Context managers for spans and resource-scoped work."""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator


@dataclass
class Span:
    name: str
    elapsed_s: float = 0.0


@contextmanager
def timer_span(name: str) -> Iterator[Span]:
    span = Span(name=name)
    start = time.perf_counter()
    try:
        yield span
    finally:
        span.elapsed_s = time.perf_counter() - start
