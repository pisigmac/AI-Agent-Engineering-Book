"""Recursive separator chunking (structure-aware)."""

from __future__ import annotations

from chunkkit.base import find_span, make_chunk, report_for
from chunkkit.types import ChunkReport, SourceDocument

DEFAULT_SEPARATORS: tuple[str, ...] = (
    "\n\n\n",  # major section breaks
    "\n\n",  # paragraphs
    "\n",  # lines
    ". ",  # sentences
    " ",  # words
    "",  # hard cut
)


def chunk_recursive(
    doc: SourceDocument,
    *,
    chunk_size: int = 400,
    chunk_overlap: int = 40,
    separators: tuple[str, ...] | None = None,
) -> ChunkReport:
    """Split text by trying coarse separators first, then finer ones.

    Inspired by common recursive character splitters; pure-Python, no deps.
    """
    if chunk_size < 1:
        raise ValueError("chunk_size must be >= 1")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("invalid chunk_overlap")
    seps = separators if separators is not None else DEFAULT_SEPARATORS
    text = doc.text
    if not text:
        return report_for(
            doc, "recursive", [], chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

    raw_parts = _split_recursive(text, seps, chunk_size)
    # Merge small parts and apply soft size targets
    merged = _merge_parts(raw_parts, chunk_size, chunk_overlap)
    chunks = []
    cursor = 0
    for idx, piece in enumerate(merged):
        start, end = find_span(text, piece, from_idx=cursor)
        cursor = max(cursor, end - chunk_overlap) if chunk_overlap else end
        chunks.append(
            make_chunk(doc, piece, start, end, strategy="recursive", index=idx)
        )
    return report_for(
        doc,
        "recursive",
        chunks,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=list(seps[:4]) + (["..."] if len(seps) > 4 else []),
    )


def _split_recursive(text: str, separators: tuple[str, ...], chunk_size: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if text else []
    if not separators:
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    sep = separators[0]
    rest = separators[1:]
    if sep == "":
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    parts = text.split(sep)
    # Re-attach separator to boundaries (except last) for readability
    pieces: list[str] = []
    for i, p in enumerate(parts):
        if i < len(parts) - 1:
            pieces.append(p + sep)
        else:
            if p:
                pieces.append(p)

    out: list[str] = []
    for piece in pieces:
        if len(piece) <= chunk_size:
            if piece:
                out.append(piece)
        else:
            out.extend(_split_recursive(piece, rest, chunk_size))
    return out


def _merge_parts(parts: list[str], chunk_size: int, overlap: int) -> list[str]:
    if not parts:
        return []
    merged: list[str] = []
    buf = ""
    for p in parts:
        if not buf:
            buf = p
            continue
        if len(buf) + len(p) <= chunk_size:
            buf += p
        else:
            merged.append(buf)
            if overlap > 0 and len(buf) > overlap:
                # carry tail overlap into next buffer
                tail = buf[-overlap:]
                buf = tail + p
                # if still too big, hard-cap later
                if len(buf) > chunk_size * 2:
                    # flush hard splits
                    while len(buf) > chunk_size:
                        merged.append(buf[:chunk_size])
                        buf = buf[chunk_size - overlap :]
            else:
                buf = p
    if buf:
        merged.append(buf)
    # Final pass: ensure none exceed ~2x (pathological)
    final: list[str] = []
    for m in merged:
        if len(m) <= chunk_size * 2:
            final.append(m)
        else:
            for i in range(0, len(m), chunk_size):
                final.append(m[i : i + chunk_size])
    return final
