"""Background job queue with retries and dead-letter."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
import time

@dataclass
class Job:
    id: str
    payload: dict[str, Any]
    attempts: int = 0
    max_attempts: int = 3

@dataclass
class JobQueue:
    handler: Callable[[dict[str, Any]], Any]
    pending: list[Job] = field(default_factory=list)
    done: list[dict[str, Any]] = field(default_factory=list)
    dead_letter: list[dict[str, Any]] = field(default_factory=list)
    _seq: int = 0
    def enqueue(self, payload: dict[str, Any], *, max_attempts: int = 3) -> str:
        self._seq += 1
        jid = f"job-{self._seq}"
        self.pending.append(Job(jid, payload, max_attempts=max_attempts))
        return jid
    def worker_once(self) -> dict[str, Any] | None:
        if not self.pending:
            return None
        job = self.pending.pop(0)
        job.attempts += 1
        try:
            result = self.handler(job.payload)
            row = {"id": job.id, "ok": True, "result": result, "attempts": job.attempts}
            self.done.append(row)
            return row
        except Exception as e:  # noqa: BLE001
            if job.attempts < job.max_attempts:
                self.pending.append(job)
                return {"id": job.id, "ok": False, "retrying": True, "attempts": job.attempts, "error": str(e)}
            row = {"id": job.id, "ok": False, "error": str(e), "attempts": job.attempts}
            self.dead_letter.append(row)
            return row
    def drain(self, max_loops: int = 100) -> dict[str, Any]:
        for _ in range(max_loops):
            if not self.pending:
                break
            self.worker_once()
        return {"done": len(self.done), "dead": len(self.dead_letter), "pending": len(self.pending)}
