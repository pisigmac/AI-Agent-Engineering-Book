"""In-memory vector index with metadata-aware search."""

from __future__ import annotations

from searchkit.metrics import cosine_similarity, dot
from searchkit.types import SearchHit, VectorRecord


class DimensionMismatchError(ValueError):
    pass


class ModelMismatchError(ValueError):
    pass


class VectorIndex:
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

    def clear(self) -> None:
        self._records.clear()
        self._dim = None
        self._model_id = None

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
                    f"model {record.model_id!r} != index {self._model_id!r}"
                )
        self._records[record.id] = record

    def upsert_many(self, records: list[VectorRecord]) -> None:
        for r in records:
            self.upsert(r)

    def delete(self, doc_id: str) -> bool:
        return self._records.pop(doc_id, None) is not None

    def get(self, doc_id: str) -> VectorRecord | None:
        return self._records.get(doc_id)

    def records(self) -> list[VectorRecord]:
        return list(self._records.values())

    def search(
        self,
        query_vector: list[float] | tuple[float, ...],
        *,
        k: int = 10,
        min_score: float | None = None,
        allow_ids: set[str] | None = None,
        model_id: str | None = None,
    ) -> list[SearchHit]:
        if k < 1:
            raise ValueError("k >= 1")
        if not self._records:
            return []
        assert self._dim is not None
        if len(query_vector) != self._dim:
            raise DimensionMismatchError(
                f"query dim {len(query_vector)} != index dim {self._dim}"
            )
        if model_id is not None and self._model_id and model_id != self._model_id:
            raise ModelMismatchError(f"query model {model_id!r} != {self._model_id!r}")

        scored: list[tuple[float, VectorRecord]] = []
        for rec in self._records.values():
            if allow_ids is not None and rec.id not in allow_ids:
                continue
            score = (
                dot(query_vector, rec.vector)
                if self.expect_unit_vectors
                else cosine_similarity(query_vector, rec.vector)
            )
            if min_score is not None and score < min_score:
                continue
            scored.append((float(score), rec))

        scored.sort(key=lambda t: (-t[0], t[1].id))
        hits: list[SearchHit] = []
        for rank, (score, rec) in enumerate(scored[:k], start=1):
            hits.append(
                SearchHit(
                    id=rec.id,
                    score=score,
                    text=rec.text,
                    metadata=dict(rec.metadata),
                    title=rec.title,
                    rank=rank,
                    score_components={"cosine": score},
                )
            )
        return hits
