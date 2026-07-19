"""Simple grounded QA over an in-memory document store."""

from __future__ import annotations

from dataclasses import dataclass

from llm_concepts.messages import CompletionResult
from llm_concepts.mock_llm import MockLLM, MockMode


@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    text: str


class InMemoryDocStore:
    def __init__(self, docs: list[Document] | None = None) -> None:
        self._docs = {d.doc_id: d for d in (docs or [])}

    def add(self, doc: Document) -> None:
        self._docs[doc.doc_id] = doc

    def all_text(self) -> str:
        parts = [f"# {d.title}\n{d.text}" for d in self._docs.values()]
        return "\n\n".join(parts)

    def search(self, query: str, *, limit: int = 3) -> list[Document]:
        terms = {t.lower() for t in query.split() if len(t) > 2}
        scored: list[tuple[int, Document]] = []
        for doc in self._docs.values():
            hay = f"{doc.title} {doc.text}".lower()
            score = sum(1 for t in terms if t in hay)
            if score:
                scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for _, d in scored[:limit]]


class GroundedQA:
    """Retrieve context then complete with a grounded mock model."""

    def __init__(self, store: InMemoryDocStore, llm: MockLLM | None = None) -> None:
        self.store = store
        self.llm = llm or MockLLM(mode=MockMode.GROUNDED)

    def ask(self, question: str) -> tuple[CompletionResult, list[Document]]:
        docs = self.store.search(question)
        context = "\n\n".join(f"{d.title}: {d.text}" for d in docs)
        # Force grounded mode for this path
        previous = self.llm.mode
        self.llm.mode = MockMode.GROUNDED
        try:
            result = self.llm.complete(question, context=context or None)
        finally:
            self.llm.mode = previous
        return result, docs


def default_policy_corpus() -> InMemoryDocStore:
    return InMemoryDocStore(
        [
            Document(
                "refunds",
                "Refund Policy",
                "Customers may request a refund within 30 days of purchase "
                "with a valid receipt. Digital goods are eligible only if unused.",
            ),
            Document(
                "support",
                "Support Hours",
                "Support is available Monday through Friday, 9am to 5pm local time. "
                "Emergency production issues use the on-call pager.",
            ),
            Document(
                "sla",
                "Service Level",
                "The standard uptime target is 99.9% monthly. Scheduled maintenance "
                "windows are announced 72 hours in advance.",
            ),
        ]
    )
