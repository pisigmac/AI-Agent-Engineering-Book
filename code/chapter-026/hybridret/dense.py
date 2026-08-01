"""Dense embedding retriever (offline hash encoder)."""
from __future__ import annotations
import hashlib
from hybridret.tokenize import tokenize
from hybridret.types import Document, Hit

class DenseRetriever:
    def __init__(self, dimensions: int = 128) -> None:
        self.dimensions = dimensions
        self.docs: dict[str, Document] = {}
        self.vecs: dict[str, list[float]] = {}

    def _embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dimensions
        for tok in tokenize(text) or ["__empty__"]:
            h = hashlib.blake2b(tok.encode(), digest_size=16).digest()
            idx = int.from_bytes(h[:8], "big") % self.dimensions
            sign = 1.0 if h[8] % 2 == 0 else -1.0
            vec[idx] += sign
        n = sum(x * x for x in vec) ** 0.5 or 1.0
        return [x / n for x in vec]

    def index(self, docs: list[Document]) -> int:
        for d in docs:
            self.docs[d.id] = d
            self.vecs[d.id] = self._embed(d.text)
        return len(docs)

    def search(self, query: str, *, k: int = 10) -> list[Hit]:
        if not self.docs:
            return []
        qv = self._embed(query)
        scored = []
        for doc_id, d in self.docs.items():
            sc = sum(a * b for a, b in zip(qv, self.vecs[doc_id]))
            scored.append((sc, d))
        scored.sort(key=lambda t: (-t[0], t[1].id))
        return [Hit(d.id, float(sc), d.text, dict(d.metadata), "dense", i)
                for i, (sc, d) in enumerate(scored[:k], 1)]
