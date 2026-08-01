"""Deterministic embedder for offline FAISS demos (swap for real models later)."""

from __future__ import annotations

import hashlib
import re
from typing import Sequence

import numpy as np

_TOKEN = re.compile(r"[a-z0-9]+", re.I)


class HashEmbedder:
    model_id = "faisskit-hash-v1"

    def __init__(self, dimensions: int = 64) -> None:
        if dimensions < 8:
            raise ValueError("dimensions >= 8")
        self.dimensions = dimensions

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        """Return float32 matrix (n, d), L2-normalized for IP≈cosine."""
        mat = np.zeros((len(texts), self.dimensions), dtype=np.float32)
        for i, text in enumerate(texts):
            toks = [t.lower() for t in _TOKEN.findall(text) if len(t) > 1] or ["__empty__"]
            for tok in toks:
                h = hashlib.blake2b(tok.encode(), digest_size=16).digest()
                idx = int.from_bytes(h[:8], "big") % self.dimensions
                sign = 1.0 if h[8] % 2 == 0 else -1.0
                mat[i, idx] += sign
            n = float(np.linalg.norm(mat[i]))
            if n > 0:
                mat[i] /= n
        return mat
