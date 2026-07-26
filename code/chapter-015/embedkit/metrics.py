"""Vector similarity and distance metrics."""

from __future__ import annotations

import math
from typing import Sequence

Vector = Sequence[float]


def _check_same_dim(a: Vector, b: Vector) -> None:
    if len(a) != len(b):
        raise ValueError(f"dimension mismatch: {len(a)} vs {len(b)}")
    if len(a) == 0:
        raise ValueError("vectors must be non-empty")


def l2_norm(v: Vector) -> float:
    return math.sqrt(sum(x * x for x in v))


def l2_normalize(v: Vector, *, eps: float = 1e-12) -> list[float]:
    n = l2_norm(v)
    if n < eps:
        # Zero vector: return zeros (caller may treat as degenerate).
        return [0.0] * len(v)
    return [x / n for x in v]


def dot(a: Vector, b: Vector) -> float:
    _check_same_dim(a, b)
    return sum(x * y for x, y in zip(a, b))


def cosine_similarity(a: Vector, b: Vector, *, eps: float = 1e-12) -> float:
    """Cosine similarity in [-1, 1]. Returns 0.0 if either vector is ~zero."""
    _check_same_dim(a, b)
    na, nb = l2_norm(a), l2_norm(b)
    if na < eps or nb < eps:
        return 0.0
    return dot(a, b) / (na * nb)


def euclidean_distance(a: Vector, b: Vector) -> float:
    _check_same_dim(a, b)
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
