"""ASCII / structured visualization of chunk boundaries."""

from __future__ import annotations

from chunkkit.types import Chunk, ChunkReport


def visualize_ascii(
    text: str,
    chunks: list[Chunk],
    *,
    width: int = 72,
    max_chunks: int = 20,
) -> str:
    """Render chunk spans as labeled slices for terminal inspection."""
    lines: list[str] = []
    lines.append(f"document_chars={len(text)} chunks={len(chunks)}")
    lines.append("-" * min(width, 72))
    for c in chunks[:max_chunks]:
        preview = c.text.replace("\n", " ").strip()
        if len(preview) > width:
            preview = preview[: width - 3] + "..."
        parent = f" parent={c.parent_id}" if c.parent_id else ""
        lines.append(
            f"[{c.index:02d}] {c.id} L{c.level} chars={len(c.text)} "
            f"tok~{c.token_estimate} [{c.start}:{c.end}]{parent}"
        )
        lines.append(f"     {preview}")
    if len(chunks) > max_chunks:
        lines.append(f"... {len(chunks) - max_chunks} more chunks")
    return "\n".join(lines)


def visualize_report(report: ChunkReport, source_text: str, **kwargs: object) -> str:
    header = (
        f"strategy={report.strategy} n={report.n_chunks} "
        f"avg_chars={report.avg_chars:.1f} avg_tok~{report.avg_tokens_est:.1f} "
        f"min={report.min_chars} max={report.max_chars}"
    )
    body = visualize_ascii(source_text, report.chunks, **kwargs)  # type: ignore[arg-type]
    return header + "\n" + body


def boundary_map(text: str, chunks: list[Chunk], *, density: int = 60) -> str:
    """One-line map of which regions are covered (chunk index mod 10)."""
    if not text:
        return ""
    n = len(text)
    marks = ["."] * density
    for c in chunks:
        a = int(c.start / max(n, 1) * (density - 1))
        b = int(max(c.end - 1, c.start) / max(n, 1) * (density - 1))
        for i in range(a, min(b + 1, density)):
            marks[i] = str(c.index % 10)
    return "|" + "".join(marks) + "|"
