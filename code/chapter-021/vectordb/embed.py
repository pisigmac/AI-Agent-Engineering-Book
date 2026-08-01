"""Lightweight hashing embedder so the mini DB is demoable offline."""

from __future__ import annotations

import hashlib
import re
from typing import Sequence

from vectordb.metrics import l2_normalize

_TOKEN = re.compile(r"[a-z0-9]+", re.I)


class HashEmbedder:
    model_id = "vectordb-hash-128d"

    def __init__(self, dimensions: int = 128) -> None:
        if dimensions < 8:
            raise ValueError("dimensions >= 8")
        self.dimensions = dimensions

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for text in texts:
            vec = [0.0] * self.dimensions
            toks = [t.lower() for t in _TOKEN.findall(text) if len(t) > 1] or ["__empty__"]
            for tok in toks:
                h = hashlib.blake2b(tok.encode(), digest_size=16).digest()
                idx = int.from_bytes(h[:8], "big") % self.dimensions
                sign = 1.0 if h[8] % 2 == 0 else -1.0
                vec[idx] += sign
            out.append(l2_normalize(vec))
        return out
