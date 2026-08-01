"""Parent-document retrieval: search children, return parents."""

from __future__ import annotations

from advrag.types import Document, SearchHit


class ParentChildIndex:
    """Stores parents and children; maps child hits up to parent passages."""

    def __init__(self) -> None:
        self.parents: dict[str, Document] = {}
        self.children: dict[str, Document] = {}

    def add_parent(self, parent: Document, children: list[Document]) -> None:
        self.parents[parent.id] = parent
        for ch in children:
            if ch.parent_id != parent.id:
                ch = Document(
                    id=ch.id,
                    text=ch.text,
                    metadata=dict(ch.metadata),
                    parent_id=parent.id,
                )
            self.children[ch.id] = ch

    def all_indexable(self) -> list[Document]:
        """Children preferred for indexing; fall back to parents if none."""
        if self.children:
            return list(self.children.values())
        return list(self.parents.values())

    def expand_to_parents(self, hits: list[SearchHit], *, k: int = 5) -> list[SearchHit]:
        """Dedupe by parent_id, returning parent text when available."""
        seen_parents: set[str] = set()
        out: list[SearchHit] = []
        for hit in hits:
            parent_id = hit.parent_id or hit.id
            if parent_id in seen_parents:
                continue
            seen_parents.add(parent_id)
            parent = self.parents.get(parent_id)
            if parent is not None:
                out.append(
                    SearchHit(
                        id=parent.id,
                        text=parent.text,
                        score=hit.score,
                        metadata={**parent.metadata, "via_child": hit.id},
                        parent_id=None,
                        sources=hit.sources + ("parent_expand",),
                        rank=len(out) + 1,
                    )
                )
            else:
                out.append(
                    SearchHit(
                        id=hit.id,
                        text=hit.text,
                        score=hit.score,
                        metadata=dict(hit.metadata),
                        parent_id=hit.parent_id,
                        sources=hit.sources,
                        rank=len(out) + 1,
                    )
                )
            if len(out) >= k:
                break
        return out


def split_parent_children(
    parent: Document,
    *,
    child_size: int = 180,
    overlap: int = 30,
) -> list[Document]:
    """Fixed-window children with parent_id linkage."""
    text = parent.text
    if len(text) <= child_size:
        return [
            Document(
                id=f"{parent.id}::c0",
                text=text,
                metadata={**parent.metadata, "role": "child"},
                parent_id=parent.id,
            )
        ]
    kids: list[Document] = []
    step = max(1, child_size - overlap)
    idx = 0
    for start in range(0, len(text), step):
        piece = text[start : start + child_size]
        if not piece.strip():
            continue
        kids.append(
            Document(
                id=f"{parent.id}::c{idx}",
                text=piece,
                metadata={**parent.metadata, "role": "child", "offset": start},
                parent_id=parent.id,
            )
        )
        idx += 1
        if start + child_size >= len(text):
            break
    return kids
