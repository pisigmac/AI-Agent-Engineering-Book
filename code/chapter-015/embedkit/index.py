"""In-memory vector index with linear-scan top-k search."""

from __future__ import annotations

from embedkit.metrics import cosine_similarity, dot
from embedkit.types import SearchHit, VectorRecord


class DimensionMismatchError(ValueError):
    """Query vector dim does not match the index."""


class ModelMismatchError(ValueError):
    """Query model_id does not match indexed vectors."""


class InMemoryVectorIndex:
    """Brute-force index. Correct and simple; swap for ANN at scale."""

    def __init__(self, *, expect_unit_vectors: bool = True) -> None:
        self._records: dict[str, VectorRecord] = {}
        self.expect_unit_vectors = expect_unit_vectors
        self._dim: int | None = None
        self._model_id: str | None = None

    def __len__(self) -> int:
        return len(self._records)

    @property
    def dimensions(self) -> int | None:
        return self._dim

    @property
    def model_id(self) -> str | None:
        return self._model_id

    def upsert(self, record: VectorRecord) -> None:
        if self._dim is None:
            self._dim = record.dim
            self._model_id = record.model_id
        else:
            if record.dim != self._dim:
                raise DimensionMismatchError(
                    f"record dim {record.dim} != index dim {self._dim}"
                )
            if record.model_id != self._model_id:
                raise ModelMismatchError(
                    f"record model {record.model_id!r} != index model {self._model_id!r}"
                )
        self._records[record.id] = record

    def upsert_many(self, records: list[VectorRecord]) -> None:
        for r in records:
            self.upsert(r)

    def get(self, doc_id: str) -> VectorRecord | None:
        return self._records.get(doc_id)

    def ids(self) -> list[str]:
        return list(self._records.keys())

    def clear(self) -> None:
        self._records.clear()
        self._dim = None
        self._model_id = None

    def search(
        self,
        query_vector: list[float] | tuple[float, ...],
        *,
        k: int = 5,
        min_score: float | None = None,
        model_id: str | None = None,
    ) -> list[SearchHit]:
        if k < 1:
            raise ValueError("k must be >= 1")
        if not self._records:
            return []
        assert self._dim is not None
        if len(query_vector) != self._dim:
            raise DimensionMismatchError(
                f"query dim {len(query_vector)} != index dim {self._dim}"
            )
        if model_id is not None and self._model_id is not None and model_id != self._model_id:
            raise ModelMismatchError(
                f"query model {model_id!r} != index model {self._model_id!r}"
            )

        scored: list[tuple[float, VectorRecord]] = []
        for rec in self._records.values():
            if self.expect_unit_vectors:
                score = dot(query_vector, rec.vector)
            else:
                score = cosine_similarity(query_vector, rec.vector)
            if min_score is not None and score < min_score:
                continue
            scored.append((score, rec))

        scored.sort(key=lambda t: t[0], reverse=True)
        hits: list[SearchHit] = []
        for score, rec in scored[:k]:
            hits.append(
                SearchHit(
                    id=rec.id,
                    score=float(score),
                    text=rec.text,
                    metadata=dict(rec.metadata),
                    model_id=rec.model_id,
                )
            )
        return hits
