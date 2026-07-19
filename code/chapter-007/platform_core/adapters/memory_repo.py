"""In-memory run repository adapter."""

from __future__ import annotations

from platform_core.domain import RunRecord


class InMemoryRunRepository:
    def __init__(self) -> None:
        self._items: dict[str, RunRecord] = {}

    def save(self, run: RunRecord) -> None:
        self._items[run.run_id] = run

    def get(self, run_id: str) -> RunRecord | None:
        return self._items.get(run_id)

    def __len__(self) -> int:
        return len(self._items)
