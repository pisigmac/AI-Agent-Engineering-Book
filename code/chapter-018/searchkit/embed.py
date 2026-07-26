"""Local embedding models for offline semantic search demos."""

from __future__ import annotations

import math
from typing import Protocol, Sequence, runtime_checkable

from searchkit.metrics import l2_normalize
from searchkit.normalize import normalize_text, tokenize


@runtime_checkable
class EmbeddingModel(Protocol):
    model_id: str
    dimensions: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        ...


class TfidfEmbedder:
    """Corpus-fitted TF-IDF vectors (classic IR / teaching dense proxy)."""

    def __init__(self, model_id: str = "tfidf-search-v1") -> None:
        self.model_id = model_id
        self._vocab: dict[str, int] = {}
        self._idf: list[float] = []
        self.dimensions = 0
        self._fitted = False

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    def fit(self, texts: Sequence[str]) -> TfidfEmbedder:
        docs = [tokenize(t) for t in texts]
        df: dict[str, int] = {}
        for toks in docs:
            for tok in set(toks):
                df[tok] = df.get(tok, 0) + 1
        terms = sorted(df.keys()) or ["__empty__"]
        if "__empty__" in terms and len(terms) == 1:
            df["__empty__"] = max(len(docs), 1)
        n_docs = max(len(docs), 1)
        self._vocab = {t: i for i, t in enumerate(terms)}
        self._idf = [math.log((1.0 + n_docs) / (1.0 + df[t])) + 1.0 for t in terms]
        self.dimensions = len(terms)
        self._fitted = True
        return self

    def _one(self, text: str) -> list[float]:
        if not self._fitted:
            raise RuntimeError("TfidfEmbedder.fit() required")
        tokens = tokenize(text)
        if not tokens:
            return l2_normalize([0.0] * self.dimensions)
        tf: dict[str, float] = {}
        for tok in tokens:
            if tok in self._vocab:
                tf[tok] = tf.get(tok, 0.0) + 1.0
        if not tf:
            return l2_normalize([0.0] * self.dimensions)
        vec = [0.0] * self.dimensions
        for tok, count in tf.items():
            idx = self._vocab[tok]
            vec[idx] = (1.0 + math.log(count)) * self._idf[idx]
        return l2_normalize(vec)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._one(t) for t in texts]


class HashingEmbedder:
    """Fixed-dim signed hashing of content tokens (no fit step)."""

    def __init__(self, dimensions: int = 128, model_id: str | None = None) -> None:
        if dimensions < 8:
            raise ValueError("dimensions >= 8")
        self.dimensions = dimensions
        self.model_id = model_id or f"hash-search-{dimensions}d-v1"

    def _one(self, text: str) -> list[float]:
        import hashlib

        tokens = tokenize(normalize_text(text)) or ["__empty__"]
        vec = [0.0] * self.dimensions
        for tok in tokens:
            h = hashlib.blake2b(tok.encode(), digest_size=16).digest()
            idx = int.from_bytes(h[:8], "big") % self.dimensions
            sign = 1.0 if h[8] % 2 == 0 else -1.0
            vec[idx] += sign
        return l2_normalize(vec)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._one(t) for t in texts]
