"""Index protocol shared by flat and IVF backends."""

from __future__ import annotations

from typing import Protocol

from vectordb.types import QueryHit, VectorRecord


class VectorIndex(Protocol):
    index_type: str

    def clear(self) -> None: ...
    def upsert(self, record: VectorRecord) -> None: ...
    def delete(self, doc_id: str) -> bool: ...
    def get(self, doc_id: str) -> VectorRecord | None: ...
    def __len__(self) -> int: ...
    def records(self) -> list[VectorRecord]: ...

    def search(
        self,
        query: list[float] | tuple[float, ...],
        *,
        k: int = 10,
        min_score: float | None = None,
        allow_ids: set[str] | None = None,
    ) -> tuple[list[QueryHit], int]:
        """Return (hits, n_scanned)."""
        ...
