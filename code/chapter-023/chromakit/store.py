"""High-level collection wrapper: upsert, query, filter, stats."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection

from chromakit.client import get_or_create_collection, make_client
from chromakit.types import QueryHit, QueryResult


class ChromaStore:
    """Production-shaped façade over a Chroma collection."""

    def __init__(
        self,
        collection_name: str = "knowledge_base",
        *,
        path: str | Path | None = None,
        dimensions: int = 64,
    ) -> None:
        self.client, self.backend = make_client(path=path)
        self.collection_name = collection_name
        self.dimensions = dimensions
        self.collection: Collection = get_or_create_collection(
            self.client, collection_name, dimensions=dimensions
        )

    def count(self) -> int:
        return int(self.collection.count())

    def upsert(
        self,
        ids: Sequence[str],
        documents: Sequence[str],
        metadatas: Sequence[dict[str, Any]] | None = None,
    ) -> int:
        if len(ids) != len(documents):
            raise ValueError("ids/documents length mismatch")
        metadatas = list(metadatas) if metadatas is not None else [{} for _ in ids]
        if len(metadatas) != len(ids):
            raise ValueError("metadatas length mismatch")
        # Chroma rejects empty metadata dicts in some versions — use placeholder
        clean_meta = []
        for m in metadatas:
            mm = dict(m) if m else {"_source": "chromakit"}
            clean_meta.append(mm)
        self.collection.upsert(
            ids=list(ids),
            documents=list(documents),
            metadatas=clean_meta,
        )
        return len(ids)

    def upsert_docs(self, docs: list[dict[str, Any]]) -> int:
        return self.upsert(
            [d["id"] for d in docs],
            [d["document"] if "document" in d else d["text"] for d in docs],
            [d.get("metadata") or {} for d in docs],
        )

    def delete(self, ids: Sequence[str]) -> None:
        if ids:
            self.collection.delete(ids=list(ids))

    def query(
        self,
        text: str,
        *,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> QueryResult:
        n = max(1, n_results)
        # Chroma errors if n_results > collection size
        n = min(n, max(self.count(), 1))
        kwargs: dict[str, Any] = {
            "query_texts": [text],
            "n_results": n,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where
        raw = self.collection.query(**kwargs)
        hits: list[QueryHit] = []
        ids = (raw.get("ids") or [[]])[0]
        docs = (raw.get("documents") or [[]])[0]
        metas = (raw.get("metadatas") or [[]])[0]
        dists = (raw.get("distances") or [[]])[0]
        for i, doc_id in enumerate(ids):
            hits.append(
                QueryHit(
                    id=doc_id,
                    document=docs[i] if docs and i < len(docs) else "",
                    metadata=dict(metas[i]) if metas and i < len(metas) and metas[i] else {},
                    distance=float(dists[i]) if dists and i < len(dists) else None,
                    rank=i + 1,
                )
            )
        return QueryResult(
            collection=self.collection_name,
            hits=hits,
            backend=self.backend,
            query=text,
        )

    def stats(self) -> dict[str, Any]:
        return {
            "collection": self.collection_name,
            "count": self.count(),
            "backend": self.backend,
            "dimensions": self.dimensions,
        }

    def list_collections(self) -> list[str]:
        return [c.name for c in self.client.list_collections()]
