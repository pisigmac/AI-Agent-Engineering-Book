"""Sliding-window chunking (explicit stride)."""

from __future__ import annotations

from chunkkit.base import make_chunk, report_for
from chunkkit.types import ChunkReport, SourceDocument


def chunk_sliding(
    doc: SourceDocument,
    *,
    window: int = 400,
    stride: int | None = None,
) -> ChunkReport:
    """Slide a fixed window across the document.

    Default stride = window // 2 (50% overlap).
    """
    if window < 1:
        raise ValueError("window must be >= 1")
    if stride is None:
        stride = max(1, window // 2)
    if stride < 1:
        raise ValueError("stride must be >= 1")

    text = doc.text
    if not text:
        return report_for(doc, "sliding", [], window=window, stride=stride)

    chunks = []
    i = 0
    idx = 0
    n = len(text)
    while i < n:
        end = min(i + window, n)
        piece = text[i:end]
        chunks.append(
            make_chunk(doc, piece, i, end, strategy="sliding", index=idx)
        )
        idx += 1
        if end >= n:
            break
        i += stride
        # prevent infinite loop if last window stuck
        if i >= n:
            break
    return report_for(doc, "sliding", chunks, window=window, stride=stride)
