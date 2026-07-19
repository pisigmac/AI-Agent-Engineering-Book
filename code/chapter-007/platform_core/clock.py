"""Clock port implementations."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class SystemClock:
    def time(self) -> float:
        return time.time()


@dataclass
class FakeClock:
    now: float = 0.0

    def time(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds
