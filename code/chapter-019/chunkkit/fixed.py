"""Fixed-size character chunking with optional overlap."""

from __future__ import annotations

from chunkkit.base import make_chunk, report_for
from chunkkit.types import ChunkReport, SourceDocument


def chunk_fixed(
    doc: SourceDocument,
    *,
    size: int = 400,
    overlap: int = 0,
) -> ChunkReport:
    if size < 1:
        raise ValueError("size must be >= 1")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be >= 0 and < size")

    text = doc.text
    if not text:
        return report_for(doc, "fixed", [], size=size, overlap=overlap)

    chunks = []
    i = 0
    idx = 0
    n = len(text)
    step = size - overlap
    while i < n:
        end = min(i + size, n)
        piece = text[i:end]
        chunks.append(
            make_chunk(doc, piece, i, end, strategy="fixed", index=idx)
        )
        idx += 1
        if end >= n:
            break
        i += step
    return report_for(doc, "fixed", chunks, size=size, overlap=overlap)
