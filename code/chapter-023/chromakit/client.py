"""Chroma client helpers: ephemeral vs persistent."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection

from chromakit.embeddings import HashEmbeddingFunction


def make_client(*, path: str | Path | None = None) -> tuple[ClientAPI, str]:
    """Return (client, backend_label).

    path=None → EphemeralClient (in-memory)
    path set → PersistentClient on disk
    """
    if path is None:
        return chromadb.EphemeralClient(), "ephemeral"
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(path)), f"persistent:{path}"


def get_or_create_collection(
    client: ClientAPI,
    name: str,
    *,
    dimensions: int = 64,
    metadata: dict[str, Any] | None = None,
    embedding_function: HashEmbeddingFunction | None = None,
) -> Collection:
    """Create/get a collection with offline hash embeddings by default."""
    if len(name) < 3:
        raise ValueError("collection name must be at least 3 characters")
    ef = embedding_function or HashEmbeddingFunction(dimensions=dimensions)
    meta = {"hnsw:space": "cosine"}
    if metadata:
        meta.update(metadata)
    return client.get_or_create_collection(
        name=name,
        embedding_function=ef,
        metadata=meta,
    )
