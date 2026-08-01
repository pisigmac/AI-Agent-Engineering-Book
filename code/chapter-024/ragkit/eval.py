"""Lightweight RAG eval: retrieval hit-rate + grounded flag on labeled questions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from ragkit.types import RAGAnswer


@dataclass(frozen=True)
class LabeledQuestion:
    question: str
    expected_doc_ids: tuple[str, ...]
    must_be_grounded: bool = True


DEFAULT_LABELS: list[LabeledQuestion] = [
    LabeledQuestion("How do I get my money back?", ("doc-refund",)),
    LabeledQuestion("Where is my package tracking number?", ("doc-shipping",)),
    LabeledQuestion("I forgot my password", ("doc-auth",)),
    LabeledQuestion("What does HTTP 429 mean?", ("doc-api",)),
    LabeledQuestion("How does RAG ground answers?", ("doc-rag",)),
]


def evaluate_rag(
    ask_fn: Callable[[str], RAGAnswer],
    labels: list[LabeledQuestion] | None = None,
) -> dict[str, Any]:
    labels = labels or DEFAULT_LABELS
    hits = 0
    grounded_ok = 0
    rows = []
    for lab in labels:
        ans = ask_fn(lab.question)
        top_ids = [c.doc_id for c in ans.citations]
        hit = any(e in top_ids for e in lab.expected_doc_ids)
        if hit:
            hits += 1
        g_ok = (ans.grounded == lab.must_be_grounded) if lab.must_be_grounded else True
        if lab.must_be_grounded and ans.grounded:
            grounded_ok += 1
        elif not lab.must_be_grounded:
            grounded_ok += 1
        rows.append(
            {
                "question": lab.question,
                "expected": list(lab.expected_doc_ids),
                "citations": top_ids,
                "hit": hit,
                "grounded": ans.grounded,
            }
        )
    n = max(len(labels), 1)
    return {
        "n": len(labels),
        "citation_hit_rate": round(hits / n, 4),
        "grounded_rate": round(grounded_ok / n, 4),
        "rows": rows,
    }
