"""Embedding model protocol and deterministic local implementations."""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol, Sequence, runtime_checkable

from embedkit.metrics import l2_normalize
from embedkit.normalize import normalize_text

_TOKEN = re.compile(r"[a-z0-9]+", re.I)

# Minimal stopword list so hashing demos are not dominated by "how/do/i/the".
_STOPWORDS = frozenset(
    """
    a an the and or but if in on at to for of as is are was were be been being
    it its this that these those i you he she we they me my your our their
    what which who whom how when where why do does did done have has had
    can could should would will just not no yes with from by into about over
    """.split()
)


@runtime_checkable
class EmbeddingModel(Protocol):
    """Minimal contract for embedders used by the platform."""

    model_id: str
    dimensions: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one L2-normalized vector per input text."""
        ...


def _stable_hash_to_unit_interval(key: str) -> float:
    """Map a string to (0, 1) deterministically via blake2b."""
    digest = hashlib.blake2b(key.encode("utf-8"), digest_size=8).digest()
    # Interpret as big-endian uint64, scale to (0, 1).
    n = int.from_bytes(digest, "big")
    return (n + 1) / (2**64 + 1)


class HashingEmbedder:
    """Feature-hash character n-grams into a fixed dense vector.

    Offline teaching model: stable, dependency-free, weak true semantics.
    Good enough for tiny paraphrase demos and pipeline tests.
    """

    def __init__(
        self,
        dimensions: int = 128,
        ngram_min: int = 3,
        ngram_max: int = 5,
        model_id: str | None = None,
    ) -> None:
        if dimensions < 8:
            raise ValueError("dimensions must be >= 8")
        if ngram_min < 1 or ngram_max < ngram_min:
            raise ValueError("invalid ngram range")
        self.dimensions = dimensions
        self.ngram_min = ngram_min
        self.ngram_max = ngram_max
        self.model_id = model_id or f"hashing-ngram-{dimensions}d-v1"

    def _ngrams(self, text: str) -> list[str]:
        # Pad so short strings still produce features.
        s = f"^{text}$"
        grams: list[str] = []
        for n in range(self.ngram_min, self.ngram_max + 1):
            if len(s) < n:
                continue
            for i in range(len(s) - n + 1):
                grams.append(s[i : i + n])
        if not grams:
            grams = [s]
        return grams

    def _accumulate(self, vec: list[float], feature: str, scale: float = 1.0) -> None:
        # Signed hashing: one bit picks sign for better collision behavior.
        h = hashlib.blake2b(feature.encode("utf-8"), digest_size=16).digest()
        idx = int.from_bytes(h[:8], "big") % self.dimensions
        sign = 1.0 if (h[8] % 2 == 0) else -1.0
        weight = 1.0 + _stable_hash_to_unit_interval(feature + ":w") * 0.25
        vec[idx] += sign * weight * scale

    def _content_tokens(self, normed: str) -> list[str]:
        return [t for t in _TOKEN.findall(normed) if t not in _STOPWORDS and len(t) > 1]

    def _embed_one(self, text: str) -> list[float]:
        normed = normalize_text(text)
        vec = [0.0] * self.dimensions
        tokens = self._content_tokens(normed)
        # Prefer whole content tokens for demo ranking quality.
        for tok in tokens:
            self._accumulate(vec, f"tk:{tok}", scale=3.0)
        # Bigrams help multi-word intents ("money back", "rate limit").
        for i in range(len(tokens) - 1):
            self._accumulate(vec, f"bg:{tokens[i]}_{tokens[i + 1]}", scale=2.0)
        # Character n-grams on content tokens only (morphology / partial match).
        for tok in tokens:
            for gram in self._ngrams(tok):
                self._accumulate(vec, f"ng:{gram}", scale=0.35)
        if not tokens:
            # Fall back to raw n-grams so empty-ish strings still embed.
            for gram in self._ngrams(normed):
                self._accumulate(vec, f"ng:{gram}", scale=1.0)
        return l2_normalize(vec)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        return [self._embed_one(t) for t in texts]


class BagOfWordsEmbedder:
    """Sparse bag-of-words projected into a fixed dimension via hashing.

    Emphasizes whole tokens more than character n-grams; still offline.
    """

    def __init__(self, dimensions: int = 128, model_id: str | None = None) -> None:
        if dimensions < 8:
            raise ValueError("dimensions must be >= 8")
        self.dimensions = dimensions
        self.model_id = model_id or f"bow-hash-{dimensions}d-v1"

    def _embed_one(self, text: str) -> list[float]:
        normed = normalize_text(text)
        tokens = [t for t in _TOKEN.findall(normed) if t not in _STOPWORDS and len(t) > 1]
        if not tokens:
            tokens = ["__empty__"]
        vec = [0.0] * self.dimensions
        for tok in tokens:
            h = hashlib.blake2b(tok.encode("utf-8"), digest_size=16).digest()
            idx = int.from_bytes(h[:8], "big") % self.dimensions
            sign = 1.0 if (h[8] % 2 == 0) else -1.0
            vec[idx] += sign
        return l2_normalize(vec)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        return [self._embed_one(t) for t in texts]


def tokenize(text: str) -> list[str]:
    """Shared content tokenizer for local lexical embedders."""
    normed = normalize_text(text)
    return [t for t in _TOKEN.findall(normed) if t not in _STOPWORDS and len(t) > 1]


class TfidfEmbedder:
    """Corpus-fitted TF-IDF vectors (classic IR embedding).

    Best offline default for the chapter mini project: no hash collisions,
    transparent IDF weighting, same model_id for docs and queries after fit.
    """

    def __init__(self, model_id: str = "tfidf-local-v1") -> None:
        self.model_id = model_id
        self._vocab: dict[str, int] = {}
        self._idf: list[float] = []
        self.dimensions = 0
        self._fitted = False

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    def fit(self, texts: Sequence[str]) -> TfidfEmbedder:
        docs_tokens = [tokenize(t) for t in texts]
        df: dict[str, int] = {}
        for toks in docs_tokens:
            for tok in set(toks):
                df[tok] = df.get(tok, 0) + 1
        # Stable dimension order.
        terms = sorted(df.keys())
        if not terms:
            terms = ["__empty__"]
            df["__empty__"] = max(len(docs_tokens), 1)
        n_docs = max(len(docs_tokens), 1)
        self._vocab = {t: i for i, t in enumerate(terms)}
        self._idf = [math.log((1.0 + n_docs) / (1.0 + df[t])) + 1.0 for t in terms]
        self.dimensions = len(terms)
        self._fitted = True
        return self

    def _embed_one(self, text: str) -> list[float]:
        if not self._fitted:
            raise RuntimeError("TfidfEmbedder.fit() required before embed()")
        tokens = tokenize(text)
        if not tokens:
            return l2_normalize([0.0] * self.dimensions)
        tf: dict[str, float] = {}
        for tok in tokens:
            if tok in self._vocab:
                tf[tok] = tf.get(tok, 0.0) + 1.0
        if not tf:
            return l2_normalize([0.0] * self.dimensions)
        # Sublinear TF.
        vec = [0.0] * self.dimensions
        for tok, count in tf.items():
            idx = self._vocab[tok]
            vec[idx] = (1.0 + math.log(count)) * self._idf[idx]
        return l2_normalize(vec)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        return [self._embed_one(t) for t in texts]
