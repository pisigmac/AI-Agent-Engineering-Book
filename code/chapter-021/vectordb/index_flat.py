"""Exact flat (brute-force) index — gold standard for recall."""

from __future__ import annotations

from vectordb.metrics import dot
from vectordb.types import QueryHit, VectorRecord


class FlatIndex:
    index_type = "flat"

    def __init__(self) -> None:
        self._records: dict[str, VectorRecord] = {}
        self.dimensions: int | None = None

    def clear(self) -> None:
        self._records.clear()
        self.dimensions = None

    def __len__(self) -> int:
        return len(self._records)

    def upsert(self, record: VectorRecord) -> None:
        dim = len(record.vector)
        if self.dimensions is None:
            self.dimensions = dim
        elif dim != self.dimensions:
            raise ValueError(f"dim {dim} != index dim {self.dimensions}")
        self._records[record.id] = record

    def delete(self, doc_id: str) -> bool:
        return self._records.pop(doc_id, None) is not None

    def get(self, doc_id: str) -> VectorRecord | None:
        return self._records.get(doc_id)

    def records(self) -> list[VectorRecord]:
        return list(self._records.values())

    def search(
        self,
        query: list[float] | tuple[float, ...],
        *,
        k: int = 10,
        min_score: float | None = None,
        allow_ids: set[str] | None = None,
    ) -> tuple[list[QueryHit], int]:
        if k < 1:
            raise ValueError("k >= 1")
        if self.dimensions is not None and len(query) != self.dimensions:
            raise ValueError(f"query dim {len(query)} != {self.dimensions}")
        scored: list[tuple[float, VectorRecord]] = []
        scanned = 0
        for rec in self._records.values():
            if allow_ids is not None and rec.id not in allow_ids:
                continue
            scanned += 1
            score = float(dot(query, rec.vector))
            if min_score is not None and score < min_score:
                continue
            scored.append((score, rec))
        scored.sort(key=lambda t: (-t[0], t[1].id))
        hits = [
            QueryHit(
                id=rec.id,
                score=score,
                metadata=dict(rec.metadata),
                text=rec.text,
                rank=i,
            )
            for i, (score, rec) in enumerate(scored[:k], start=1)
        ]
        return hits, scanned
