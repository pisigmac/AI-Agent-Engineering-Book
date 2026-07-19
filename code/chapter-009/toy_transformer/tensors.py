"""Minimal pure-Python vector/matrix helpers for the toy model."""

from __future__ import annotations

import math
import random
from typing import Iterable


Vector = list[float]
Matrix = list[list[float]]


def zeros(n: int) -> Vector:
    return [0.0] * n


def zeros_mat(rows: int, cols: int) -> Matrix:
    return [zeros(cols) for _ in range(rows)]


def rand_vec(n: int, *, scale: float = 0.1, rng: random.Random | None = None) -> Vector:
    r = rng or random.Random(0)
    return [r.uniform(-scale, scale) for _ in range(n)]


def rand_mat(rows: int, cols: int, *, scale: float = 0.1, rng: random.Random | None = None) -> Matrix:
    return [rand_vec(cols, scale=scale, rng=rng) for _ in range(rows)]


def matvec(a: Matrix, x: Vector) -> Vector:
    return [sum(a[i][j] * x[j] for j in range(len(x))) for i in range(len(a))]


def matmul(a: Matrix, b: Matrix) -> Matrix:
    if not a or not b:
        return []
    n, m, p = len(a), len(a[0]), len(b[0])
    out = zeros_mat(n, p)
    for i in range(n):
        for k in range(m):
            aik = a[i][k]
            for j in range(p):
                out[i][j] += aik * b[k][j]
    return out


def transpose(a: Matrix) -> Matrix:
    if not a:
        return []
    return [[a[i][j] for i in range(len(a))] for j in range(len(a[0]))]


def add_vec(a: Vector, b: Vector) -> Vector:
    return [x + y for x, y in zip(a, b, strict=True)]


def add_mat(a: Matrix, b: Matrix) -> Matrix:
    return [add_vec(ra, rb) for ra, rb in zip(a, b, strict=True)]


def scale_vec(v: Vector, s: float) -> Vector:
    return [x * s for x in v]


def softmax(xs: Vector) -> Vector:
    m = max(xs) if xs else 0.0
    exps = [math.exp(x - m) for x in xs]
    s = sum(exps) or 1.0
    return [e / s for e in exps]


def argmax(xs: Vector) -> int:
    best_i = 0
    best_v = xs[0] if xs else float("-inf")
    for i, v in enumerate(xs):
        if v > best_v:
            best_v = v
            best_i = i
    return best_i


def layer_norm(x: Vector, eps: float = 1e-5) -> Vector:
    n = len(x) or 1
    mean = sum(x) / n
    var = sum((v - mean) ** 2 for v in x) / n
    inv = 1.0 / math.sqrt(var + eps)
    return [(v - mean) * inv for v in x]


def apply_row_fn(mat: Matrix, fn) -> Matrix:
    return [fn(row) for row in mat]
