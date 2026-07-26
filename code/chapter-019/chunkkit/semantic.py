"""Semantic chunking via sentence similarity breakpoints."""

from __future__ import annotations

import re
from collections import Counter

from chunkkit.base import find_span, make_chunk, report_for
from chunkkit.types import ChunkReport, SourceDocument

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n{2,}")


def _sentences(text: str) -> list[str]:
    parts = [p.strip() for p in _SENT_SPLIT.split(text) if p and p.strip()]
    return parts if parts else ([text] if text else [])


def _bow(text: str) -> Counter[str]:
    toks = re.findall(r"[a-z0-9]+", text.lower())
    return Counter(t for t in toks if len(t) > 1)


def _cosine_bow(a: Counter[str], b: Counter[str]) -> float:
    if not a or not b:
        return 0.0
    keys = set(a) | set(b)
    dot = sum(a[k] * b[k] for k in keys)
    na = sum(v * v for v in a.values()) ** 0.5
    nb = sum(v * v for v in b.values()) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def chunk_semantic(
    doc: SourceDocument,
    *,
    similarity_threshold: float = 0.25,
    max_chunk_chars: int = 600,
    min_chunk_chars: int = 80,
) -> ChunkReport:
    """Group consecutive sentences while adjacent similarity stays high.

    Offline bag-of-words cosine between neighboring sentences — teaching stand-in
    for embedding-based semantic splitters.
    """
    if not (0.0 <= similarity_threshold <= 1.0):
        raise ValueError("similarity_threshold in [0,1]")
    if max_chunk_chars < 1:
        raise ValueError("max_chunk_chars must be >= 1")

    text = doc.text
    sents = _sentences(text)
    if not sents:
        return report_for(
            doc,
            "semantic",
            [],
            similarity_threshold=similarity_threshold,
            max_chunk_chars=max_chunk_chars,
        )

    groups: list[list[str]] = [[sents[0]]]
    sims: list[float] = []
    for i in range(1, len(sents)):
        sim = _cosine_bow(_bow(sents[i - 1]), _bow(sents[i]))
        sims.append(sim)
        cur = groups[-1]
        cur_len = sum(len(x) for x in cur) + len(cur)  # spaces
        # Break on topic shift or size cap
        if sim < similarity_threshold or cur_len + len(sents[i]) > max_chunk_chars:
            groups.append([sents[i]])
        else:
            cur.append(sents[i])

    # Merge tiny trailing groups into previous when possible
    merged_groups: list[list[str]] = []
    for g in groups:
        piece = " ".join(g)
        if (
            merged_groups
            and len(piece) < min_chunk_chars
            and sum(len(x) for x in merged_groups[-1]) + len(piece) <= max_chunk_chars
        ):
            merged_groups[-1].extend(g)
        else:
            merged_groups.append(g)

    chunks = []
    cursor = 0
    for idx, g in enumerate(merged_groups):
        piece = " ".join(g).strip()
        start, end = find_span(text, g[0], from_idx=cursor)
        # Better end: find last sentence
        _, end2 = find_span(text, g[-1], from_idx=start)
        end = max(end, end2)
        # Prefer exact join length if find fails badly
        if end <= start:
            start, end = find_span(text, piece, from_idx=cursor)
        cursor = end
        chunks.append(
            make_chunk(
                doc,
                piece,
                start,
                end,
                strategy="semantic",
                index=idx,
                extra_meta={"n_sentences": len(g)},
            )
        )

    avg_sim = sum(sims) / len(sims) if sims else 0.0
    return report_for(
        doc,
        "semantic",
        chunks,
        similarity_threshold=similarity_threshold,
        max_chunk_chars=max_chunk_chars,
        avg_adjacent_sim=round(avg_sim, 4),
        n_breakpoints=sum(1 for s in sims if s < similarity_threshold),
    )
