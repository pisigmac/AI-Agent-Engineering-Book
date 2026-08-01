"""Offline embedding function for Chroma (no ONNX model download)."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from chromadb.api.types import Documents, EmbeddingFunction, Embeddings, Space

_TOKEN = re.compile(r"[a-z0-9]+", re.I)


class HashEmbeddingFunction(EmbeddingFunction[Documents]):
    """Deterministic bag-of-tokens hashing — CI-friendly stand-in for MiniLM."""

    def __init__(self, dimensions: int = 64) -> None:
        if dimensions < 8:
            raise ValueError("dimensions must be >= 8")
        self.dimensions = dimensions

    @staticmethod
    def name() -> str:
        return "chromakit-hash"

    def get_config(self) -> dict[str, Any]:
        return {"dimensions": self.dimensions}

    @staticmethod
    def build_from_config(config: dict[str, Any]) -> HashEmbeddingFunction:
        return HashEmbeddingFunction(dimensions=int(config.get("dimensions", 64)))

    def default_space(self) -> Space:
        return "cosine"

    def __call__(self, input: Documents) -> Embeddings:
        out: Embeddings = []
        for text in input:
            vec = [0.0] * self.dimensions
            toks = [t.lower() for t in _TOKEN.findall(text) if len(t) > 1] or ["__empty__"]
            for tok in toks:
                h = hashlib.blake2b(tok.encode("utf-8"), digest_size=16).digest()
                idx = int.from_bytes(h[:8], "big") % self.dimensions
                sign = 1.0 if h[8] % 2 == 0 else -1.0
                vec[idx] += sign
            norm = sum(x * x for x in vec) ** 0.5 or 1.0
            out.append([x / norm for x in vec])
        return out
