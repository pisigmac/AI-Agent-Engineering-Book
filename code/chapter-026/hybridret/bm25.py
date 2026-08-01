"""BM25 sparse lexical retriever."""
from __future__ import annotations
import math
from collections import Counter, defaultdict
from hybridret.tokenize import tokenize
from hybridret.types import Document, Hit

class BM25Retriever:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1, self.b = k1, b
        self.docs: dict[str, Document] = {}
        self.tf: dict[str, Counter[str]] = {}
        self.df: dict[str, int] = defaultdict(int)
        self.dl: dict[str, int] = {}
        self.avgdl = 0.0
        self.n = 0

    def index(self, docs: list[Document]) -> int:
        for d in docs:
            toks = tokenize(d.text)
            tf = Counter(toks)
            self.docs[d.id] = d
            self.tf[d.id] = tf
            self.dl[d.id] = max(len(toks), 1)
            for t in tf:
                self.df[t] += 1
        self.n = len(self.docs)
        self.avgdl = sum(self.dl.values()) / max(self.n, 1)
        return len(docs)

    def _idf(self, term: str) -> float:
        df = self.df.get(term, 0)
        return math.log(1 + (self.n - df + 0.5) / (df + 0.5))

    def search(self, query: str, *, k: int = 10) -> list[Hit]:
        terms = tokenize(query)
        if not terms or not self.docs:
            return []
        scores: dict[str, float] = defaultdict(float)
        for term in terms:
            idf = self._idf(term)
            for doc_id, tf in self.tf.items():
                f = tf.get(term, 0)
                if not f:
                    continue
                dl = self.dl[doc_id]
                denom = f + self.k1 * (1 - self.b + self.b * dl / max(self.avgdl, 1e-9))
                scores[doc_id] += idf * (f * (self.k1 + 1)) / denom
        ranked = sorted(scores.items(), key=lambda t: (-t[1], t[0]))[:k]
        out = []
        for i, (doc_id, sc) in enumerate(ranked, 1):
            d = self.docs[doc_id]
            out.append(Hit(d.id, float(sc), d.text, dict(d.metadata), "bm25", i))
        return out
