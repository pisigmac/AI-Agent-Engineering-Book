"""Hybrid retriever orchestrating BM25, dense, sparse + fusion."""
from __future__ import annotations
from hybridret.bm25 import BM25Retriever
from hybridret.dense import DenseRetriever
from hybridret.sparse import SparseTfidfRetriever
from hybridret.fusion import rrf, weighted_fuse
from hybridret.types import Document, Hit
from hybridret.corpus import DOCS
from hybridret.eval import evaluate
from hybridret.corpus import LABELS

class HybridRetriever:
    def __init__(self) -> None:
        self.bm25 = BM25Retriever()
        self.dense = DenseRetriever()
        self.sparse = SparseTfidfRetriever()

    def index(self, docs: list[Document] | None = None) -> int:
        docs = docs if docs is not None else list(DOCS)
        self.bm25.index(docs)
        self.dense.index(docs)
        self.sparse.index(docs)
        return len(docs)

    def search(self, query: str, *, k: int = 5, mode: str = "hybrid_rrf", candidate_k: int = 20) -> list[Hit]:
        mode = mode.lower()
        ck = max(k, candidate_k)
        if mode == "bm25":
            return self.bm25.search(query, k=k)
        if mode == "dense":
            return self.dense.search(query, k=k)
        if mode in {"sparse", "sparse_tfidf"}:
            return self.sparse.search(query, k=k)
        bm = self.bm25.search(query, k=ck)
        de = self.dense.search(query, k=ck)
        sp = self.sparse.search(query, k=ck)
        if mode in {"hybrid", "hybrid_rrf", "rrf"}:
            return rrf([bm, de, sp], k=k)
        if mode in {"hybrid_weighted", "weighted"}:
            return weighted_fuse([bm, de, sp], [0.45, 0.35, 0.20], k=k)
        raise ValueError(f"unknown mode: {mode}")

    def compare(self, query: str, *, k: int = 3) -> dict:
        modes = ["bm25", "dense", "sparse", "hybrid_rrf", "hybrid_weighted"]
        return {m: [h.to_dict() for h in self.search(query, k=k, mode=m)] for m in modes}

    def eval_modes(self, *, k: int = 3) -> dict:
        out = {}
        for mode in ["bm25", "dense", "sparse", "hybrid_rrf", "hybrid_weighted"]:
            report = evaluate(lambda q, m=mode: self.search(q, k=k, mode=m), LABELS, k=k)
            out[mode] = report.to_dict()
        return out
