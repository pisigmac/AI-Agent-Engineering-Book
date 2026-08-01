"""Minimal BM25 sparse retriever."""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from advrag.tokenize import tokenize
from advrag.types import Document, SearchHit


class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self._docs: dict[str, Document] = {}
        self._tf: dict[str, Counter[str]] = {}
        self._df: dict[str, int] = defaultdict(int)
        self._dl: dict[str, int] = {}
        self._avgdl = 0.0
        self._n = 0

    def __len__(self) -> int:
        return self._n

    def index(self, docs: list[Document]) -> int:
        for doc in docs:
            if doc.id in self._docs:
                self._remove_stats(doc.id)
            toks = tokenize(doc.text)
            tf = Counter(toks)
            self._docs[doc.id] = doc
            self._tf[doc.id] = tf
            self._dl[doc.id] = max(len(toks), 1)
            for t in tf:
                self._df[t] += 1
        self._n = len(self._docs)
        self._avgdl = sum(self._dl.values()) / max(self._n, 1)
        return len(docs)

    def _remove_stats(self, doc_id: str) -> None:
        tf = self._tf.pop(doc_id, Counter())
        self._dl.pop(doc_id, None)
        self._docs.pop(doc_id, None)
        for t in tf:
            self._df[t] = max(0, self._df[t] - 1)

    def _idf(self, term: str) -> float:
        df = self._df.get(term, 0)
        # BM25+ style smooth idf
        return math.log(1 + (self._n - df + 0.5) / (df + 0.5))

    def search(self, query: str, *, k: int = 10) -> list[SearchHit]:
        q_terms = tokenize(query)
        if not q_terms or not self._docs:
            return []
        scores: dict[str, float] = defaultdict(float)
        for term in q_terms:
            idf = self._idf(term)
            for doc_id, tf in self._tf.items():
                f = tf.get(term, 0)
                if f == 0:
                    continue
                dl = self._dl[doc_id]
                denom = f + self.k1 * (1 - self.b + self.b * dl / max(self._avgdl, 1e-9))
                scores[doc_id] += idf * (f * (self.k1 + 1)) / denom
        ranked = sorted(scores.items(), key=lambda t: (-t[1], t[0]))[:k]
        hits: list[SearchHit] = []
        for i, (doc_id, score) in enumerate(ranked, start=1):
            doc = self._docs[doc_id]
            hits.append(
                SearchHit(
                    id=doc.id,
                    text=doc.text,
                    score=float(score),
                    metadata=dict(doc.metadata),
                    parent_id=doc.parent_id,
                    sources=("bm25",),
                    rank=i,
                )
            )
        return hits
