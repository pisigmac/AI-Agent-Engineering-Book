"""Citation construction from ranked chunks."""

from __future__ import annotations

from ragkit.types import Citation, RetrievedChunk


def build_citations(chunks: list[RetrievedChunk], *, max_snippet: int = 180) -> list[Citation]:
    cites: list[Citation] = []
    for i, ch in enumerate(chunks, start=1):
        title = str(ch.metadata.get("title") or ch.id)
        snippet = ch.text.strip().replace("\n", " ")
        if len(snippet) > max_snippet:
            snippet = snippet[: max_snippet - 3] + "..."
        score = ch.ranker_score if ch.ranker_score is not None else ch.score
        cites.append(
            Citation(
                index=i,
                doc_id=ch.id,
                title=title,
                snippet=snippet,
                score=float(score),
            )
        )
    return cites


def format_citation_footer(citations: list[Citation]) -> str:
    if not citations:
        return ""
    lines = ["Sources:"]
    for c in citations:
        lines.append(f"[{c.index}] {c.title} ({c.doc_id})")
    return "\n".join(lines)
