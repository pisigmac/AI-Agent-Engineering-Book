"""Scaling primitives: job queue, workers, horizontal fan-out."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable
import itertools

JobFn = Callable[[dict[str, Any]], dict[str, Any]]

@dataclass
class Job:
    id: str
    payload: dict[str, Any]

@dataclass
class WorkerPool:
    handler: JobFn
    max_workers: int = 4
    completed: list[dict[str, Any]] = field(default_factory=list)

    def map(self, jobs: list[Job]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futs = {pool.submit(self._run, job): job.id for job in jobs}
            for fut in as_completed(futs):
                jid = futs[fut]
                try:
                    out = fut.result()
                    row = {"id": jid, "ok": True, "result": out}
                except Exception as e:  # noqa: BLE001
                    row = {"id": jid, "ok": False, "error": str(e)}
                results.append(row)
                self.completed.append(row)
        results.sort(key=lambda r: r["id"])
        return results

    def _run(self, job: Job) -> dict[str, Any]:
        return self.handler(job.payload)

def shard_goals(goals: list[str], *, shards: int = 2) -> list[list[str]]:
    shards = max(1, shards)
    buckets: list[list[str]] = [[] for _ in range(shards)]
    for i, g in enumerate(goals):
        buckets[i % shards].append(g)
    return buckets

def demo_scale(goals: list[str] | None = None) -> dict[str, Any]:
    goals = goals or [f"task-{i}" for i in range(6)]
    def handle(p: dict[str, Any]) -> dict[str, Any]:
        return {"echo": p.get("goal"), "worker": True}
    jobs = [Job(id=f"job-{i}", payload={"goal": g}) for i, g in enumerate(goals)]
    pool = WorkerPool(handle, max_workers=3)
    results = pool.map(jobs)
    return {"shards": shard_goals(goals, shards=3), "results": results, "n_ok": sum(1 for r in results if r["ok"])}
