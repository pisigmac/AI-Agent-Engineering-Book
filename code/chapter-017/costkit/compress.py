"""Cheap text compression heuristics to shrink prompt tokens (demo-grade)."""

from __future__ import annotations

import re
from dataclasses import dataclass

_WS = re.compile(r"\s+")
_DUP_NL = re.compile(r"\n{3,}")


@dataclass(frozen=True)
class CompressResult:
    original: str
    compressed: str
    original_chars: int
    compressed_chars: int

    @property
    def ratio(self) -> float:
        if self.original_chars == 0:
            return 1.0
        return self.compressed_chars / self.original_chars

    @property
    def saved_chars(self) -> int:
        return max(0, self.original_chars - self.compressed_chars)

    def to_dict(self) -> dict:
        return {
            "original_chars": self.original_chars,
            "compressed_chars": self.compressed_chars,
            "ratio": round(self.ratio, 4),
            "saved_chars": self.saved_chars,
            "compressed_preview": self.compressed[:200],
        }


def compress_text(
    text: str,
    *,
    max_chars: int | None = None,
    strip_bullets: bool = False,
) -> CompressResult:
    """Whitespace collapse + optional truncation. Not a substitute for summarization."""
    out = text.strip()
    out = _DUP_NL.sub("\n\n", out)
    out = _WS.sub(" ", out.replace("\t", " "))
    # restore paragraph breaks roughly
    out = out.replace(" \n ", "\n").replace(" \n", "\n").replace("\n ", "\n")
    if strip_bullets:
        lines = []
        for line in out.split("\n"):
            lines.append(re.sub(r"^[\-\*\u2022]\s+", "", line.strip()))
        out = "\n".join(lines)
    if max_chars is not None and len(out) > max_chars:
        out = out[: max_chars - 3].rstrip() + "..."
    return CompressResult(
        original=text,
        compressed=out,
        original_chars=len(text),
        compressed_chars=len(out),
    )


def estimate_tokens(text: str) -> int:
    return 0 if not text else max(1, len(text) // 4)
