"""Multi-collection vector database façade."""

from __future__ import annotations

from typing import Any

from vectordb.collection import Collection


class VectorDB:
    """In-process mini vector DB — swap storage later, keep this API."""

    def __init__(self) -> None:
        self._collections: dict[str, Collection] = {}

    def create_collection(
        self,
        name: str,
        *,
        index_type: str = "flat",
        dimensions: int | None = None,
        model_id: str = "external",
        nlist: int = 8,
        nprobe: int = 2,
        exist_ok: bool = False,
    ) -> Collection:
        if name in self._collections:
            if exist_ok:
                return self._collections[name]
            raise ValueError(f"collection exists: {name}")
        col = Collection(
            name,
            index_type=index_type,
            dimensions=dimensions,
            model_id=model_id,
            nlist=nlist,
            nprobe=nprobe,
        )
        self._collections[name] = col
        return col

    def get_collection(self, name: str) -> Collection:
        try:
            return self._collections[name]
        except KeyError as exc:
            raise KeyError(f"unknown collection: {name}") from exc

    def delete_collection(self, name: str) -> bool:
        return self._collections.pop(name, None) is not None

    def list_collections(self) -> list[str]:
        return sorted(self._collections)

    def stats(self) -> dict[str, Any]:
        return {
            "collections": [self._collections[n].stats().to_dict() for n in self.list_collections()]
        }
