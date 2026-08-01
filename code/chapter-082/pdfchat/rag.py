"""Document-grounded Q&A with lexical retrieval and citation packing."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
import re
import math


def simple_chunk(text: str, *, size: int = 200, overlap: int = 40) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks: list[str] = []
    i = 0
    while i < len(text):
        chunks.append(text[i : i + size])
        i += max(1, size - overlap)
    return chunks


@dataclass
class Chunk:
    doc_id: str
    chunk_id: int
    text: str
    page: int = 1

    @property
    def citation(self) -> str:
        return f"{self.doc_id}#p{self.page}/c{self.chunk_id}"


def _tokens(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", s.lower()))


@dataclass
class InMemoryIndex:
    chunks: list[Chunk] = field(default_factory=list)

    def add(self, doc_id: str, text: str, *, page: int = 1) -> int:
        parts = simple_chunk(text)
        for i, p in enumerate(parts):
            self.chunks.append(Chunk(doc_id=doc_id, chunk_id=i, text=p, page=page))
        return len(parts)

    def search(self, query: str, *, k: int = 3) -> list[tuple[float, Chunk]]:
        q = _tokens(query)
        if not q:
            return []
        scored: list[tuple[float, Chunk]] = []
        for c in self.chunks:
            t = _tokens(c.text)
            if not t:
                continue
            inter = len(q & t)
            union = len(q | t)
            score = inter / union if union else 0.0
            # prefer denser matches
            score += 0.01 * inter
            if score > 0:
                scored.append((score, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:k]


class LLM(Protocol):
    def complete(self, prompt: str) -> str: ...


@dataclass
class MockLLM:
    def complete(self, prompt: str) -> str:
        # echo a short grounded answer marker
        return f"[grounded] {prompt[-120:]}"


@dataclass
class PdfChat:
    index: InMemoryIndex
    llm: LLM
    events: list[dict[str, Any]] = field(default_factory=list)

    def ingest(self, doc_id: str, text: str, *, page: int = 1) -> dict[str, Any]:
        n = self.index.add(doc_id, text, page=page)
        ev = {"type": "ingest", "doc_id": doc_id, "chunks": n}
        self.events.append(ev)
        return ev

    def ask(self, question: str, *, k: int = 3) -> dict[str, Any]:
        hits = self.index.search(question, k=k)
        context = "\n---\n".join(f"[{c.citation}] {c.text}" for _, c in hits)
        prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer with citations."
        answer = self.llm.complete(prompt)
        citations = [c.citation for _, c in hits]
        out = {
            "answer": answer,
            "citations": citations,
            "scores": [round(s, 4) for s, _ in hits],
        }
        self.events.append({"type": "ask", "q": question, "n_hits": len(hits)})
        return out
