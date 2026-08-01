"""Priority job scheduler (cron-like interval + priority queue)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
import heapq, itertools

@dataclass(order=True)
class ScheduledJob:
    priority: int
    seq: int
    name: str = field(compare=False)
    interval_s: float = field(compare=False, default=0)
    next_run: float = field(compare=False, default=0)
    fn: Callable[[], Any] = field(compare=False, default=lambda: None)

class Scheduler:
    def __init__(self) -> None:
        self._hq: list[ScheduledJob] = []
        self._seq = itertools.count()
        self.now = 0.0
        self.history: list[str] = []
    def schedule(self, name: str, fn: Callable[[], Any], *, priority: int = 100, interval_s: float = 0, delay_s: float = 0) -> None:
        job = ScheduledJob(priority, next(self._seq), name, interval_s, self.now + delay_s, fn)
        heapq.heappush(self._hq, job)
    def tick(self, dt: float = 1.0) -> list[str]:
        self.now += dt
        ran = []
        ready = []
        while self._hq and self._hq[0].next_run <= self.now + 1e-9:
            ready.append(heapq.heappop(self._hq))
        # higher priority first among ready (lower number)
        ready.sort()
        for job in ready:
            job.fn(); ran.append(job.name); self.history.append(job.name)
            if job.interval_s > 0:
                job.next_run = self.now + job.interval_s
                heapq.heappush(self._hq, job)
        return ran
