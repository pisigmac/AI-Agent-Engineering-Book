"""Semantic search service: pipeline + index façade for the platform."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from embedkit.corpus import load_support_corpus
from embedkit.index import InMemoryVectorIndex
from embedkit.metrics import cosine_similarity
from embedkit.models import EmbeddingModel, TfidfEmbedder
from embedkit.pipeline import EmbeddingPipeline
from embedkit.types import Document, SearchHit


@dataclass
class SearchResult:
    query: str
    hits: list[SearchHit]
    model_id: str
    index_size: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "model_id": self.model_id,
            "index_size": self.index_size,
            "hits": [h.to_dict() for h in self.hits],
        }


@dataclass
class SemanticSearch:
    """High-level API used by CLI and future retrieval chapters."""

    pipeline: EmbeddingPipeline
    index: InMemoryVectorIndex = field(default_factory=InMemoryVectorIndex)

    @classmethod
    def with_model(cls, model: EmbeddingModel | None = None) -> SemanticSearch:
        """Build a search service. Default model is an unfitted TfidfEmbedder
        (fitted automatically on first index_documents call)."""
        model = model or TfidfEmbedder()
        return cls(pipeline=EmbeddingPipeline(model))

    def index_documents(self, docs: list[Document] | None = None) -> int:
        docs = docs if docs is not None else load_support_corpus()
        model = self.pipeline.model
        if isinstance(model, TfidfEmbedder) and not model.is_fitted:
            model.fit([d.text for d in docs])
            # dimensions may have changed after fit — rebuild pipeline binding
            self.pipeline = EmbeddingPipeline(model)
        records = self.pipeline.embed_documents(docs)
        self.index.upsert_many(records)
        return len(records)

    def search(
        self,
        query: str,
        *,
        k: int = 3,
        min_score: float | None = None,
    ) -> SearchResult:
        qvec = self.pipeline.embed_query(query)
        hits = self.index.search(
            qvec,
            k=k,
            min_score=min_score,
            model_id=self.pipeline.model_id,
        )
        return SearchResult(
            query=query,
            hits=hits,
            model_id=self.pipeline.model_id,
            index_size=len(self.index),
        )

    def similarity(self, text_a: str, text_b: str) -> float:
        va, vb = self.pipeline.embed_texts([text_a, text_b])
        return cosine_similarity(va, vb)


def build_default_search() -> SemanticSearch:
    """Index the sample support corpus with the default hashing embedder."""
    svc = SemanticSearch.with_model()
    svc.index_documents()
    return svc
