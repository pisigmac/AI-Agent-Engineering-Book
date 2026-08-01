"""Hybrid BM25 + dense retrieval with RRF fusion."""

from __future__ import annotations

from advrag.bm25 import BM25Index
from advrag.dense import DenseIndex
from advrag.fusion import reciprocal_rank_fusion
from advrag.types import Document, SearchHit


class HybridRetriever:
    def __init__(self, *, candidate_k: int = 20) -> None:
        self.bm25 = BM25Index()
        self.dense = DenseIndex()
        self.candidate_k = candidate_k

    def index(self, docs: list[Document]) -> int:
        self.bm25.index(docs)
        self.dense.index(docs)
        return len(docs)

    def search(
        self,
        query: str,
        *,
        k: int = 5,
        mode: str = "hybrid",
    ) -> list[SearchHit]:
        mode = mode.lower()
        ck = max(k, self.candidate_k)
        if mode == "bm25":
            return self.bm25.search(query, k=k)
        if mode == "dense":
            return self.dense.search(query, k=k)
        # hybrid
        sparse = self.bm25.search(query, k=ck)
        dense = self.dense.search(query, k=ck)
        return reciprocal_rank_fusion([sparse, dense], k=k)
