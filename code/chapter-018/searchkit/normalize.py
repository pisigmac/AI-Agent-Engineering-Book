"""Text normalization for consistent embeddings."""

from __future__ import annotations

import re
import unicodedata

_WS = re.compile(r"\s+")
_TOKEN = re.compile(r"[a-z0-9]+", re.I)

STOPWORDS = frozenset(
    """
    a an the and or but if in on at to for of as is are was were be been being
    it its this that these those i you he she we they me my your our their
    what which who whom how when where why do does did done have has had
    can could should would will just not no yes with from by into about over
    """.split()
)


def normalize_text(text: str, *, lowercase: bool = True) -> str:
    out = unicodedata.normalize("NFKC", text).strip()
    if lowercase:
        out = out.lower()
    return _WS.sub(" ", out)


def tokenize(text: str) -> list[str]:
    normed = normalize_text(text)
    return [t for t in _TOKEN.findall(normed) if t not in STOPWORDS and len(t) > 1]
