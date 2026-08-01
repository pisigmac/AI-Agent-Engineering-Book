"""High-level FAISS index service with metadata and search."""

from __future__ import annotations

import time
from typing import Any, Sequence

import faiss
import numpy as np

from faisskit.embed import HashEmbedder
from faisskit.indexes import build_index, set_ef_search, set_nprobe, train_if_needed
from faisskit.store import DocStore
from faisskit.types import IndexKind, IndexStats, SearchHit, SearchResult


class FaissIndexService:
    """Production-shaped wrapper: embed → add → search → persist-ready state."""

    def __init__(
        self,
        *,
        kind: str | IndexKind = IndexKind.FLAT_IP,
        dimensions: int = 64,
        embedder: HashEmbedder | None = None,
        nlist: int = 16,
        nprobe: int = 4,
        hnsw_m: int = 32,
        ef_search: int = 16,
    ) -> None:
        self.embedder = embedder or HashEmbedder(dimensions)
        self.dimensions = self.embedder.dimensions
        self.store = DocStore()
        self._index, self._params = build_index(
            kind,
            self.dimensions,
            nlist=nlist,
            nprobe=nprobe,
            hnsw_m=hnsw_m,
            ef_search=ef_search,
        )
        self._kind = IndexKind(kind)

    @property
    def ntotal(self) -> int:
        return int(self._index.ntotal)

    def add_texts(
        self,
        ids: Sequence[str],
        texts: Sequence[str],
        metadatas: Sequence[dict[str, Any]] | None = None,
    ) -> int:
        if len(ids) != len(texts):
            raise ValueError("ids/texts length mismatch")
        metadatas = metadatas or [{} for _ in ids]
        if len(metadatas) != len(ids):
            raise ValueError("metadatas length mismatch")

        vectors = self.embedder.embed(list(texts))
        train_if_needed(self._index, vectors)

        int_ids = []
        for doc_id, text, meta in zip(ids, texts, metadatas):
            # re-add: remove old vector if present
            old = self.store.int_id(doc_id)
            if old is not None:
                try:
                    self._index.remove_ids(np.array([old], dtype=np.int64))
                except Exception:
                    pass
            iid = self.store.add(doc_id, text, meta)
            int_ids.append(iid)

        id_arr = np.array(int_ids, dtype=np.int64)
        self._index.add_with_ids(np.ascontiguousarray(vectors, dtype=np.float32), id_arr)
        return len(ids)

    def add_documents(self, docs: list[dict[str, Any]]) -> int:
        return self.add_texts(
            [d["id"] for d in docs],
            [d["text"] for d in docs],
            [d.get("metadata") or {} for d in docs],
        )

    def remove(self, doc_id: str) -> bool:
        iid = self.store.remove(doc_id)
        if iid is None:
            return False
        self._index.remove_ids(np.array([iid], dtype=np.int64))
        return True

    def configure(self, *, nprobe: int | None = None, ef_search: int | None = None) -> None:
        if nprobe is not None:
            set_nprobe(self._index, nprobe)
            self._params["nprobe"] = nprobe
        if ef_search is not None:
            set_ef_search(self._index, ef_search)
            self._params["efSearch"] = ef_search

    def search(
        self,
        query: str,
        *,
        k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> SearchResult:
        t0 = time.perf_counter()
        if self.ntotal == 0:
            return SearchResult(hits=[], index_kind=self._kind.value, ntotal=0, took_ms=0.0, query=query)

        q = self.embedder.embed([query])
        # over-fetch if filtering
        fetch_k = k if not where else min(self.ntotal, max(k * 5, k))
        scores, ids = self._index.search(np.ascontiguousarray(q, dtype=np.float32), fetch_k)
        hits: list[SearchHit] = []
        for score, iid in zip(scores[0], ids[0]):
            if iid < 0:
                continue
            doc = self.store.get_by_int(int(iid))
            if doc is None:
                continue
            meta = doc["metadata"]
            if where and not all(meta.get(kk) == vv for kk, vv in where.items()):
                continue
            hits.append(
                SearchHit(
                    id=doc["id"],
                    score=float(score),
                    text=doc["text"],
                    metadata=dict(meta),
                    rank=0,
                )
            )
            if len(hits) >= k:
                break
        for i, h in enumerate(hits, start=1):
            hits[i - 1] = SearchHit(
                id=h.id, score=h.score, text=h.text, metadata=h.metadata, rank=i
            )
        took = (time.perf_counter() - t0) * 1000
        return SearchResult(
            hits=hits,
            index_kind=self._kind.value,
            ntotal=self.ntotal,
            took_ms=took,
            query=query,
        )

    def stats(self) -> IndexStats:
        metric = self._params.get("metric", "ip")
        return IndexStats(
            kind=self._kind.value,
            dimensions=self.dimensions,
            ntotal=self.ntotal,
            metric=metric,
            params=dict(self._params),
        )

    def raw_index(self) -> faiss.Index:
        return self._index
