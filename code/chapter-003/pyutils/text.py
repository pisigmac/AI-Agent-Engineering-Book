"""Pure text helpers for platform boundaries."""

from __future__ import annotations

import re

from pyutils.errors import ValidationError

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def clamp(value: float, *, lo: float, hi: float) -> float:
    if lo > hi:
        raise ValidationError("lo must be <= hi")
    return max(lo, min(hi, value))


def slugify(text: str, *, max_len: int = 48) -> str:
    if max_len <= 0:
        raise ValidationError("max_len must be positive")
    s = text.strip().lower()
    s = _SLUG_RE.sub("-", s).strip("-")
    if not s:
        raise ValidationError("cannot slugify empty text")
    return s[:max_len].rstrip("-")


def truncate(text: str, max_chars: int, *, suffix: str = "…") -> str:
    if max_chars < 0:
        raise ValidationError("max_chars must be >= 0")
    if len(text) <= max_chars:
        return text
    if max_chars == 0:
        return ""
    keep = max(0, max_chars - len(suffix))
    return text[:keep] + suffix
