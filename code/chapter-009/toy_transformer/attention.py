"""Causal scaled dot-product attention (toy implementation)."""

from __future__ import annotations

import math

from toy_transformer.tensors import Matrix, Vector, matmul, softmax, transpose, zeros_mat


NEG_INF = -1e9


def causal_mask(n: int) -> Matrix:
    """Return additive mask: 0 allowed, large negative for forbidden future positions."""
    mask = zeros_mat(n, n)
    for i in range(n):
        for j in range(n):
            if j > i:
                mask[i][j] = NEG_INF
    return mask


def scaled_dot_product_attention(
    q: Matrix,
    k: Matrix,
    v: Matrix,
    *,
    mask: Matrix | None = None,
    return_weights: bool = False,
) -> Matrix | tuple[Matrix, Matrix]:
    """
    q,k,v: [T, d]
    returns output [T, d] and optionally weights [T, T]
    """
    t = len(q)
    d = len(q[0]) if q else 1
    scale = 1.0 / math.sqrt(max(d, 1))
    # scores = q @ k^T
    scores = matmul(q, transpose(k))
    for i in range(t):
        for j in range(t):
            scores[i][j] *= scale
            if mask is not None:
                scores[i][j] += mask[i][j]

    weights: Matrix = [softmax(row) for row in scores]
    # out = weights @ v
    out = matmul(weights, v)
    if return_weights:
        return out, weights
    return out


def project(x: Matrix, w: Matrix, b: Vector | None = None) -> Matrix:
    """x [T,d_in], w [d_out, d_in] -> [T, d_out] via row-wise matvec-like multiply."""
    # Implement as x @ w^T
    out = matmul(x, transpose(w))
    if b is not None:
        out = [[out[i][j] + b[j] for j in range(len(b))] for i in range(len(out))]
    return out
