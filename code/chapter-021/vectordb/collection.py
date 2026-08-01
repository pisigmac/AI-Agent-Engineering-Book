"""Named collection: embed optional, upsert, query with filters."""

from __future__ import annotations

import time
from typing import Any

from vectordb.embed import HashEmbedder
from vectordb.filter import matches
from vectordb.index_flat import FlatIndex
from vectordb.index_ivf import IVFIndex
from vectordb.metrics import l2_normalize
from vectordb.types import CollectionStats, QueryResult, VectorRecord


class Collection:
    def __init__(
        self,
        name: str,
        *,
        index_type: str = "flat",
        dimensions: int | None = None,
        model_id: str = "external",
        nlist: int = 8,
        nprobe: int = 2,
    ) -> None:
        self.name = name
        self.model_id = model_id
        self._dimensions = dimensions
        self._index_type = index_type
        if index_type == "flat":
            self._index: FlatIndex | IVFIndex = FlatIndex()
        elif index_type == "ivf":
            self._index = IVFIndex(nlist=nlist, nprobe=nprobe)
        else:
            raise ValueError("index_type must be 'flat' or 'ivf'")
        self._embedder = HashEmbedder(dimensions or 128)

    @property
    def index_type(self) -> str:
        return self._index.index_type

    def __len__(self) -> int:
        return len(self._index)

    def upsert(
        self,
        *,
        id: str,
        vector: list[float] | tuple[float, ...] | None = None,
        text: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if vector is None:
            if not text:
                raise ValueError("provide vector or text")
            vector = self._embedder.embed([text])[0]
            self.model_id = self._embedder.model_id
        else:
            vector = l2_normalize(vector)
        rec = VectorRecord(
            id=id,
            vector=tuple(vector),
            metadata=dict(metadata or {}),
            text=text,
        )
        if self._dimensions is None:
            self._dimensions = len(rec.vector)
        self._index.upsert(rec)

    def upsert_many(self, rows: list[dict[str, Any]]) -> int:
        for row in rows:
            self.upsert(
                id=row["id"],
                vector=row.get("vector"),
                text=row.get("text", ""),
                metadata=row.get("metadata"),
            )
        return len(rows)

    def delete(self, doc_id: str) -> bool:
        return self._index.delete(doc_id)

    def get(self, doc_id: str) -> VectorRecord | None:
        return self._index.get(doc_id)

    def query(
        self,
        *,
        vector: list[float] | tuple[float, ...] | None = None,
        text: str | None = None,
        k: int = 5,
        min_score: float | None = None,
        where: dict[str, Any] | None = None,
    ) -> QueryResult:
        t0 = time.perf_counter()
        if vector is None:
            if not text:
                raise ValueError("provide vector or text")
            vector = self._embedder.embed([text])[0]
        else:
            vector = l2_normalize(vector)

        allow: set[str] | None = None
        if where:
            allow = {
                r.id
                for r in self._index.records()
                if matches(r.metadata, where)
            }

        hits, scanned = self._index.search(
            vector, k=k, min_score=min_score, allow_ids=allow
        )
        took = (time.perf_counter() - t0) * 1000
        return QueryResult(
            collection=self.name,
            hits=hits,
            index_type=self.index_type,
            n_scanned=scanned,
            took_ms=took,
            filters=where or {},
        )

    def stats(self) -> CollectionStats:
        keys: set[str] = set()
        for r in self._index.records():
            keys.update(r.metadata.keys())
        return CollectionStats(
            name=self.name,
            count=len(self._index),
            dimensions=self._dimensions or getattr(self._index, "dimensions", None),
            index_type=self.index_type,
            model_id=self.model_id,
            metadata_keys=sorted(keys),
        )

    def rebuild(self) -> None:
        if isinstance(self._index, IVFIndex):
            self._index.build()
