"""Runnable offline embedders for benchmarking (not production neural quality)."""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from typing import Sequence

from embbench.metrics import l2_normalize

_TOKEN = re.compile(r"[a-z0-9\u00c0-\u024f]+", re.I)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text) if len(t) > 1]


class TfidfEmbedder:
    model_id = "teaching:tfidf"
    dimensions = 0

    def __init__(self) -> None:
        self._vocab: dict[str, int] = {}
        self._idf: list[float] = []
        self._fitted = False

    def fit(self, texts: Sequence[str]) -> TfidfEmbedder:
        docs = [tokenize(t) for t in texts]
        df: Counter[str] = Counter()
        for toks in docs:
            df.update(set(toks))
        terms = sorted(df.keys()) or ["__empty__"]
        n = max(len(docs), 1)
        self._vocab = {t: i for i, t in enumerate(terms)}
        self._idf = [math.log((1 + n) / (1 + df[t])) + 1.0 for t in terms]
        self.dimensions = len(terms)
        self._fitted = True
        return self

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not self._fitted:
            raise RuntimeError("fit() required for TfidfEmbedder")
        out: list[list[float]] = []
        for text in texts:
            tf: Counter[str] = Counter(tokenize(text))
            vec = [0.0] * self.dimensions
            for tok, c in tf.items():
                if tok in self._vocab:
                    i = self._vocab[tok]
                    vec[i] = (1.0 + math.log(c)) * self._idf[i]
            out.append(l2_normalize(vec))
        return out


class HashingEmbedder:
    def __init__(self, dimensions: int = 256, model_id: str = "teaching:hashing") -> None:
        self.dimensions = dimensions
        self.model_id = model_id

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for text in texts:
            vec = [0.0] * self.dimensions
            for tok in tokenize(text) or ["__empty__"]:
                h = hashlib.blake2b(tok.encode("utf-8"), digest_size=16).digest()
                idx = int.from_bytes(h[:8], "big") % self.dimensions
                sign = 1.0 if h[8] % 2 == 0 else -1.0
                vec[idx] += sign
            out.append(l2_normalize(vec))
        return out


class CharNgramEmbedder:
    """Character n-gram hashing — better cross-lingual surface robustness offline."""

    def __init__(
        self,
        dimensions: int = 256,
        n_min: int = 3,
        n_max: int = 5,
        model_id: str = "teaching:char-ngram",
    ) -> None:
        self.dimensions = dimensions
        self.n_min = n_min
        self.n_max = n_max
        self.model_id = model_id

    def _grams(self, text: str) -> list[str]:
        s = f"^{text.lower()}$"
        grams: list[str] = []
        for n in range(self.n_min, self.n_max + 1):
            if len(s) < n:
                continue
            for i in range(len(s) - n + 1):
                grams.append(s[i : i + n])
        return grams or ["__empty__"]

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for text in texts:
            vec = [0.0] * self.dimensions
            for g in self._grams(text):
                h = hashlib.blake2b(g.encode("utf-8"), digest_size=16).digest()
                idx = int.from_bytes(h[:8], "big") % self.dimensions
                sign = 1.0 if h[8] % 2 == 0 else -1.0
                vec[idx] += sign
            out.append(l2_normalize(vec))
        return out


def build_teaching_embedder(model_id: str):
    if model_id == "teaching:tfidf":
        return TfidfEmbedder()
    if model_id == "teaching:hashing":
        return HashingEmbedder()
    if model_id == "teaching:char-ngram":
        return CharNgramEmbedder()
    raise KeyError(f"no offline embedder for {model_id}")
