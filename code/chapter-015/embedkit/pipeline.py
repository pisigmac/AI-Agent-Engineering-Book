"""Embed documents and queries through a shared model + normalize path."""

from __future__ import annotations

from typing import Sequence

from embedkit.models import EmbeddingModel
from embedkit.normalize import normalize_text
from embedkit.types import Document, VectorRecord


class EmbeddingPipeline:
    """Owns model identity and document → VectorRecord conversion."""

    def __init__(self, model: EmbeddingModel) -> None:
        self.model = model

    @property
    def model_id(self) -> str:
        return self.model.model_id

    @property
    def dimensions(self) -> int:
        return self.model.dimensions

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        # Model implementations also normalize; pipeline normalizes once so
        # call sites that skip the model still share policy.
        prepared = [normalize_text(t) for t in texts]
        vectors = self.model.embed(prepared)
        if len(vectors) != len(prepared):
            raise RuntimeError("embedder returned wrong batch size")
        for v in vectors:
            if len(v) != self.dimensions:
                raise RuntimeError(
                    f"embedder returned dim {len(v)}, expected {self.dimensions}"
                )
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def embed_documents(self, docs: Sequence[Document]) -> list[VectorRecord]:
        if not docs:
            return []
        vectors = self.embed_texts([d.text for d in docs])
        records: list[VectorRecord] = []
        for doc, vec in zip(docs, vectors):
            meta = dict(doc.metadata)
            meta.setdefault("source", "document")
            records.append(
                VectorRecord(
                    id=doc.id,
                    vector=tuple(vec),
                    text=doc.text,
                    metadata=meta,
                    model_id=self.model_id,
                    dim=self.dimensions,
                )
            )
        return records
