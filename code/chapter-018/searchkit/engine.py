"""Semantic search engine: ingest, filter, rank, explain, evaluate."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from searchkit.corpus import knowledge_base, labeled_queries
from searchkit.embed import EmbeddingModel, TfidfEmbedder
from searchkit.eval import evaluate
from searchkit.index import VectorIndex
from searchkit.rank import apply_metadata_boosts, mmr_rerank
from searchkit.store import DocumentStore
from searchkit.types import (
    Document,
    EvalReport,
    SearchHit,
    SearchResponse,
    VectorRecord,
)


@dataclass
class SearchEngine:
    """Production-shaped offline search engine for the platform."""

    store: DocumentStore = field(default_factory=DocumentStore)
    index: VectorIndex = field(default_factory=VectorIndex)
    model: EmbeddingModel = field(default_factory=TfidfEmbedder)

    @classmethod
    def with_defaults(cls) -> SearchEngine:
        eng = cls()
        eng.ingest(knowledge_base())
        return eng

    def _ensure_fitted(self, docs: list[Document]) -> None:
        model = self.model
        if isinstance(model, TfidfEmbedder) and not model.is_fitted:
            model.fit([d.text for d in docs] or ["__empty__"])

    def ingest(self, docs: list[Document], *, rebuild: bool = False) -> int:
        if rebuild:
            self.store = DocumentStore()
            self.index.clear()
            if isinstance(self.model, TfidfEmbedder):
                self.model = TfidfEmbedder(model_id=self.model.model_id)
        self.store.upsert_many(docs)
        all_docs = self.store.all()
        self._ensure_fitted(all_docs)
        # Re-embed all when using fitted models after rebuild or first fit
        if rebuild or isinstance(self.model, TfidfEmbedder):
            self.index.clear()
            vectors = self.model.embed([d.text for d in all_docs])
            for doc, vec in zip(all_docs, vectors):
                self.index.upsert(
                    VectorRecord(
                        id=doc.id,
                        vector=tuple(vec),
                        text=doc.text,
                        metadata=dict(doc.metadata),
                        model_id=self.model.model_id,
                        dim=len(vec),
                        title=doc.title,
                    )
                )
        else:
            new_docs = docs
            vectors = self.model.embed([d.text for d in new_docs])
            for doc, vec in zip(new_docs, vectors):
                self.index.upsert(
                    VectorRecord(
                        id=doc.id,
                        vector=tuple(vec),
                        text=doc.text,
                        metadata=dict(doc.metadata),
                        model_id=self.model.model_id,
                        dim=len(vec),
                        title=doc.title,
                    )
                )
        return len(docs)

    def delete(self, doc_id: str) -> bool:
        a = self.store.delete(doc_id)
        b = self.index.delete(doc_id)
        return a or b

    def search(
        self,
        query: str,
        *,
        k: int = 5,
        min_score: float | None = None,
        filters: dict[str, Any] | None = None,
        strategy: str = "cosine",
        candidate_k: int | None = None,
        boosts: dict[str, dict[object, float]] | None = None,
        mmr_lambda: float = 0.7,
    ) -> SearchResponse:
        t0 = time.perf_counter()
        filters = filters or {}
        allow = self.store.filter_ids(**filters) if filters else None
        qvec = self.model.embed([query])[0]
        pool = candidate_k or max(k * 4, k)
        raw = self.index.search(
            qvec,
            k=pool,
            min_score=min_score,
            allow_ids=allow,
            model_id=self.model.model_id,
        )

        if strategy == "mmr":
            recs = {r.id: r for r in self.index.records()}
            hits = mmr_rerank(raw, recs, qvec, lambda_mult=mmr_lambda, k=k)
        elif strategy == "boost":
            hits = apply_metadata_boosts(raw, boosts=boosts)
            hits = hits[:k]
        else:
            hits = raw[:k]
            # re-rank numbers
            hits = [
                SearchHit(
                    id=h.id,
                    score=h.score,
                    text=h.text,
                    metadata=h.metadata,
                    title=h.title,
                    rank=i,
                    score_components=h.score_components,
                )
                for i, h in enumerate(hits, start=1)
            ]

        took = (time.perf_counter() - t0) * 1000
        return SearchResponse(
            query=query,
            hits=hits,
            model_id=self.model.model_id,
            index_size=len(self.index),
            filters=filters,
            took_ms=took,
            strategy=strategy,
        )

    def explain(self, query: str, doc_id: str) -> dict[str, Any]:
        """Explain similarity components for a query/document pair."""
        rec = self.index.get(doc_id)
        doc = self.store.get(doc_id)
        if rec is None or doc is None:
            return {"ok": False, "error": "unknown_doc", "doc_id": doc_id}
        qvec = self.model.embed([query])[0]
        from searchkit.metrics import cosine_similarity, dot
        from searchkit.normalize import tokenize

        score = dot(qvec, rec.vector)
        q_toks = set(tokenize(query))
        d_toks = set(tokenize(doc.text))
        overlap = sorted(q_toks & d_toks)
        return {
            "ok": True,
            "query": query,
            "doc_id": doc_id,
            "title": doc.title,
            "cosine": score,
            "token_overlap": overlap,
            "query_tokens": sorted(q_toks),
            "doc_token_sample": sorted(d_toks)[:30],
            "metadata": doc.metadata,
            "model_id": self.model.model_id,
        }

    def evaluate_default(self, *, k: int = 3) -> EvalReport:
        def _search(q: str) -> list[SearchHit]:
            return self.search(q, k=k).hits

        return evaluate(labeled_queries(), _search, k=k)

    def stats(self) -> dict[str, Any]:
        topics: dict[str, int] = {}
        for d in self.store.all():
            t = str(d.metadata.get("topic", "unknown"))
            topics[t] = topics.get(t, 0) + 1
        return {
            "documents": len(self.store),
            "vectors": len(self.index),
            "model_id": self.model.model_id,
            "dimensions": getattr(self.model, "dimensions", None),
            "topics": topics,
        }
