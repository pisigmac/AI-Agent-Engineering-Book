"""Stable text preprocessing before embedding."""

from __future__ import annotations

import re
import unicodedata

_WS = re.compile(r"\s+")


def normalize_text(text: str, *, lowercase: bool = True, collapse_ws: bool = True) -> str:
    """Normalize Unicode and optional whitespace/case for consistent embeddings.

    Production systems should version this function alongside model_id.
    """
    if not isinstance(text, str):
        raise TypeError("text must be str")
    # NFKC folds compatibility characters (e.g. full-width) into canonical forms.
    out = unicodedata.normalize("NFKC", text).strip()
    if lowercase:
        out = out.lower()
    if collapse_ws:
        out = _WS.sub(" ", out)
    return out


def normalize_batch(texts: list[str], **kwargs: object) -> list[str]:
    return [normalize_text(t, **kwargs) for t in texts]  # type: ignore[arg-type]
