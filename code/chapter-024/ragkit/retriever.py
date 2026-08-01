"""Dense retriever with metadata filters (in-memory, FAISS/Chroma-swappable)."""

from __future__ import annotations

from typing import Any, Protocol

from ragkit.embed import HashEmbedder, dot
from ragkit.types import Document, RetrievedChunk


class Retriever(Protocol):
    def index(self, docs: list[Document]) -> int: ...
    def retrieve(
        self,
        query: str,
        *,
        k: int = 5,
        where: dict[str, Any] | None = None,
        min_score: float | None = None,
    ) -> list[RetrievedChunk]: ...


class InMemoryRetriever:
    """Production-shaped retriever API backed by brute-force cosine search."""

    def __init__(self, embedder: HashEmbedder | None = None) -> None:
        self.embedder = embedder or HashEmbedder()
        self._docs: dict[str, Document] = {}
        self._vectors: dict[str, list[float]] = {}

    def __len__(self) -> int:
        return len(self._docs)

    def index(self, docs: list[Document]) -> int:
        if not docs:
            return 0
        vectors = self.embedder.embed([d.text for d in docs])
        for doc, vec in zip(docs, vectors):
            self._docs[doc.id] = doc
            self._vectors[doc.id] = vec
        return len(docs)

    def retrieve(
        self,
        query: str,
        *,
        k: int = 5,
        where: dict[str, Any] | None = None,
        min_score: float | None = None,
    ) -> list[RetrievedChunk]:
        if k < 1:
            raise ValueError("k >= 1")
        if not self._docs:
            return []
        qv = self.embedder.embed([query])[0]
        scored: list[tuple[float, Document]] = []
        for doc_id, doc in self._docs.items():
            if where and not all(doc.metadata.get(kk) == vv for kk, vv in where.items()):
                continue
            score = float(dot(qv, self._vectors[doc_id]))
            if min_score is not None and score < min_score:
                continue
            scored.append((score, doc))
        scored.sort(key=lambda t: (-t[0], t[1].id))
        hits: list[RetrievedChunk] = []
        for i, (score, doc) in enumerate(scored[:k], start=1):
            hits.append(
                RetrievedChunk(
                    id=doc.id,
                    text=doc.text,
                    score=score,
                    metadata=dict(doc.metadata),
                    rank=i,
                )
            )
        return hits
