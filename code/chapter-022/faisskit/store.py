"""Sidecar store: string ids ↔ int64 FAISS ids + metadata/text."""

from __future__ import annotations

from typing import Any


class DocStore:
    """FAISS only stores vectors + int64 ids; we keep the rest here."""

    def __init__(self) -> None:
        self._by_str: dict[str, dict[str, Any]] = {}
        self._str_to_int: dict[str, int] = {}
        self._int_to_str: dict[int, str] = {}
        self._next_id = 1

    def __len__(self) -> int:
        return len(self._by_str)

    def add(
        self,
        doc_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        if doc_id in self._str_to_int:
            iid = self._str_to_int[doc_id]
        else:
            iid = self._next_id
            self._next_id += 1
            self._str_to_int[doc_id] = iid
            self._int_to_str[iid] = doc_id
        self._by_str[doc_id] = {
            "id": doc_id,
            "text": text,
            "metadata": dict(metadata or {}),
            "int_id": iid,
        }
        return iid

    def remove(self, doc_id: str) -> int | None:
        if doc_id not in self._str_to_int:
            return None
        iid = self._str_to_int.pop(doc_id)
        self._int_to_str.pop(iid, None)
        self._by_str.pop(doc_id, None)
        return iid

    def get(self, doc_id: str) -> dict[str, Any] | None:
        return self._by_str.get(doc_id)

    def get_by_int(self, iid: int) -> dict[str, Any] | None:
        sid = self._int_to_str.get(int(iid))
        return self._by_str.get(sid) if sid else None

    def int_id(self, doc_id: str) -> int | None:
        return self._str_to_int.get(doc_id)

    def all_docs(self) -> list[dict[str, Any]]:
        return list(self._by_str.values())

    def to_dict(self) -> dict[str, Any]:
        return {
            "next_id": self._next_id,
            "docs": self._by_str,
            "str_to_int": self._str_to_int,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocStore:
        store = cls()
        store._next_id = int(data.get("next_id", 1))
        store._by_str = dict(data.get("docs") or {})
        store._str_to_int = {k: int(v) for k, v in (data.get("str_to_int") or {}).items()}
        store._int_to_str = {int(v): k for k, v in store._str_to_int.items()}
        return store
