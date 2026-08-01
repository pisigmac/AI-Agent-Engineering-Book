"""Dense cosine retriever (hash embeddings)."""

from __future__ import annotations

import hashlib
from typing import Sequence

from advrag.tokenize import tokenize
from advrag.types import Document, SearchHit


class HashEmbedder:
    def __init__(self, dimensions: int = 128) -> None:
        self.dimensions = dimensions

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for text in texts:
            vec = [0.0] * self.dimensions
            for tok in tokenize(text) or ["__empty__"]:
                h = hashlib.blake2b(tok.encode(), digest_size=16).digest()
                idx = int.from_bytes(h[:8], "big") % self.dimensions
                sign = 1.0 if h[8] % 2 == 0 else -1.0
                vec[idx] += sign
            n = sum(x * x for x in vec) ** 0.5 or 1.0
            out.append([x / n for x in vec])
        return out


class DenseIndex:
    def __init__(self, dimensions: int = 128) -> None:
        self.embedder = HashEmbedder(dimensions)
        self._docs: dict[str, Document] = {}
        self._vecs: dict[str, list[float]] = {}

    def __len__(self) -> int:
        return len(self._docs)

    def index(self, docs: list[Document]) -> int:
        if not docs:
            return 0
        vecs = self.embedder.embed([d.text for d in docs])
        for d, v in zip(docs, vecs):
            self._docs[d.id] = d
            self._vecs[d.id] = v
        return len(docs)

    def search(self, query: str, *, k: int = 10) -> list[SearchHit]:
        if not self._docs:
            return []
        qv = self.embedder.embed([query])[0]
        scored: list[tuple[float, Document]] = []
        for doc_id, doc in self._docs.items():
            score = sum(a * b for a, b in zip(qv, self._vecs[doc_id]))
            scored.append((score, doc))
        scored.sort(key=lambda t: (-t[0], t[1].id))
        hits = []
        for i, (score, doc) in enumerate(scored[:k], start=1):
            hits.append(
                SearchHit(
                    id=doc.id,
                    text=doc.text,
                    score=float(score),
                    metadata=dict(doc.metadata),
                    parent_id=doc.parent_id,
                    sources=("dense",),
                    rank=i,
                )
            )
        return hits
