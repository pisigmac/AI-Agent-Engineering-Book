"""Knowledge assistant: retrieve from Chroma + grounded extractive answer."""

from __future__ import annotations

from typing import Any

from chromakit.corpus import knowledge_docs
from chromakit.store import ChromaStore
from chromakit.types import AssistantAnswer, QueryHit


def _extractive_answer(query: str, hits: list[QueryHit]) -> tuple[str, bool]:
    """Offline grounded answer without calling an LLM.

    Uses the top hit text; refuses if empty or distance too high.
    """
    if not hits:
        return (
            "I could not find relevant knowledge base passages for that question.",
            False,
        )
    top = hits[0]
    # distance for cosine space in Chroma is often 1 - cosine; keep a soft gate
    if top.distance is not None and top.distance > 0.85:
        return (
            "I found only weakly related passages. Please rephrase or contact support.",
            False,
        )
    cite = top.metadata.get("title") or top.id
    answer = (
        f"Based on {cite}: {top.document.strip()}"
    )
    if len(hits) > 1:
        extra = hits[1].metadata.get("title") or hits[1].id
        answer += f" (See also: {extra}.)"
    return answer, True


class KnowledgeAssistant:
    """Mini product: ingest KB → Chroma retrieve → cited answer."""

    def __init__(self, store: ChromaStore | None = None, **store_kwargs: Any) -> None:
        self.store = store or ChromaStore("knowledge_base", **store_kwargs)

    def ingest_default(self) -> int:
        return self.store.upsert_docs(knowledge_docs())

    def ask(
        self,
        question: str,
        *,
        n_results: int = 3,
        where: dict[str, Any] | None = None,
    ) -> AssistantAnswer:
        result = self.store.query(question, n_results=n_results, where=where)
        answer, grounded = _extractive_answer(question, result.hits)
        citations = [
            {
                "id": h.id,
                "title": h.metadata.get("title"),
                "topic": h.metadata.get("topic"),
                "distance": h.distance,
                "snippet": h.document[:160],
            }
            for h in result.hits
        ]
        return AssistantAnswer(
            answer=answer,
            citations=citations,
            grounded=grounded,
            query=question,
            collection=self.store.collection_name,
        )
