"""Explicit sparse TF-IDF vector retrieval (complement to BM25)."""
from __future__ import annotations
import math
from collections import Counter, defaultdict
from hybridret.tokenize import tokenize
from hybridret.types import Document, Hit

class SparseTfidfRetriever:
    def __init__(self) -> None:
        self.docs: dict[str, Document] = {}
        self.vocab: dict[str, int] = {}
        self.idf: list[float] = []
        self.vecs: dict[str, list[float]] = {}

    def index(self, docs: list[Document]) -> int:
        tokenized = {d.id: tokenize(d.text) for d in docs}
        df: dict[str, int] = defaultdict(int)
        for toks in tokenized.values():
            for t in set(toks):
                df[t] += 1
        terms = sorted(df) or ["__empty__"]
        n = max(len(docs), 1)
        self.vocab = {t: i for i, t in enumerate(terms)}
        self.idf = [math.log((1 + n) / (1 + df.get(t, 0))) + 1.0 for t in terms]
        self.docs = {d.id: d for d in docs}
        dim = len(terms)
        for d in docs:
            tf = Counter(tokenized[d.id])
            vec = [0.0] * dim
            for t, c in tf.items():
                if t in self.vocab:
                    i = self.vocab[t]
                    vec[i] = (1 + math.log(c)) * self.idf[i]
            nrm = sum(x * x for x in vec) ** 0.5 or 1.0
            self.vecs[d.id] = [x / nrm for x in vec]
        return len(docs)

    def _qvec(self, query: str) -> list[float]:
        tf = Counter(tokenize(query))
        dim = len(self.vocab)
        vec = [0.0] * dim
        for t, c in tf.items():
            if t in self.vocab:
                i = self.vocab[t]
                vec[i] = (1 + math.log(c)) * self.idf[i]
        nrm = sum(x * x for x in vec) ** 0.5 or 1.0
        return [x / nrm for x in vec]

    def search(self, query: str, *, k: int = 10) -> list[Hit]:
        if not self.docs:
            return []
        qv = self._qvec(query)
        scored = []
        for doc_id, d in self.docs.items():
            sc = sum(a * b for a, b in zip(qv, self.vecs[doc_id]))
            scored.append((sc, d))
        scored.sort(key=lambda t: (-t[0], t[1].id))
        return [Hit(d.id, float(sc), d.text, dict(d.metadata), "sparse_tfidf", i)
                for i, (sc, d) in enumerate(scored[:k], 1)]
