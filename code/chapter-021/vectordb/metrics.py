"""Vector similarity helpers (unit cosine via dot)."""

from __future__ import annotations

import math
from typing import Sequence

Vector = Sequence[float]


def l2_normalize(v: Vector, *, eps: float = 1e-12) -> list[float]:
    n = math.sqrt(sum(x * x for x in v))
    if n < eps:
        return [0.0] * len(v)
    return [x / n for x in v]


def dot(a: Vector, b: Vector) -> float:
    if len(a) != len(b):
        raise ValueError(f"dim mismatch {len(a)} vs {len(b)}")
    return sum(x * y for x, y in zip(a, b))
