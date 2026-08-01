"""Offline hash embedder for the RAG retriever."""

from __future__ import annotations

import hashlib
import re
from typing import Sequence

_TOKEN = re.compile(r"[a-z0-9]+", re.I)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text) if len(t) > 1]


class HashEmbedder:
    model_id = "ragkit-hash-128d"

    def __init__(self, dimensions: int = 128) -> None:
        if dimensions < 8:
            raise ValueError("dimensions >= 8")
        self.dimensions = dimensions

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for text in texts:
            vec = [0.0] * self.dimensions
            for tok in tokenize(text) or ["__empty__"]:
                h = hashlib.blake2b(tok.encode(), digest_size=16).digest()
                idx = int.from_bytes(h[:8], "big") % self.dimensions
                sign = 1.0 if h[8] % 2 == 0 else -1.0
                vec[idx] += sign
            n = sum(x * x for x in vec) ** 0.5 or 1.0
            out.append([x / n for x in vec])
        return out


def dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))
