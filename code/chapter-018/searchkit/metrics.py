"""Vector similarity helpers."""

from __future__ import annotations

import math
from typing import Sequence

Vector = Sequence[float]


def l2_norm(v: Vector) -> float:
    return math.sqrt(sum(x * x for x in v))


def l2_normalize(v: Vector, *, eps: float = 1e-12) -> list[float]:
    n = l2_norm(v)
    if n < eps:
        return [0.0] * len(v)
    return [x / n for x in v]


def dot(a: Vector, b: Vector) -> float:
    if len(a) != len(b):
        raise ValueError(f"dimension mismatch: {len(a)} vs {len(b)}")
    return sum(x * y for x, y in zip(a, b))


def cosine_similarity(a: Vector, b: Vector, *, eps: float = 1e-12) -> float:
    na, nb = l2_norm(a), l2_norm(b)
    if na < eps or nb < eps:
        return 0.0
    return dot(a, b) / (na * nb)
