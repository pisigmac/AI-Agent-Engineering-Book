"""Document store with metadata indexing."""

from __future__ import annotations

from searchkit.types import Document


class DocumentStore:
    """Source-of-truth documents; vectors live in the index."""

    def __init__(self) -> None:
        self._docs: dict[str, Document] = {}

    def __len__(self) -> int:
        return len(self._docs)

    def upsert(self, doc: Document) -> None:
        self._docs[doc.id] = doc

    def upsert_many(self, docs: list[Document]) -> int:
        for d in docs:
            self.upsert(d)
        return len(docs)

    def get(self, doc_id: str) -> Document | None:
        return self._docs.get(doc_id)

    def delete(self, doc_id: str) -> bool:
        return self._docs.pop(doc_id, None) is not None

    def all(self) -> list[Document]:
        return list(self._docs.values())

    def ids(self) -> list[str]:
        return list(self._docs.keys())

    def filter_ids(self, **metadata_equals: object) -> set[str]:
        """Return ids whose metadata contains all key=value pairs."""
        if not metadata_equals:
            return set(self._docs.keys())
        out: set[str] = set()
        for doc in self._docs.values():
            ok = True
            for k, v in metadata_equals.items():
                if doc.metadata.get(k) != v:
                    ok = False
                    break
            if ok:
                out.add(doc.id)
        return out
