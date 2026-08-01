"""Shared tokenization for BM25 / hybrid."""

from __future__ import annotations

import re

_TOKEN = re.compile(r"[a-z0-9]+", re.I)

STOP = frozenset(
    """
    a an the and or but if in on at to for of as is are was were be been being
    it this that these those i you we they me my your our what which who how
    when where why do does did have has had can could should would will just
    not no with from by into about over
    """.split()
)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text) if len(t) > 1 and t.lower() not in STOP]
