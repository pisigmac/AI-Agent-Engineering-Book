"""Toy decoder stack: embeddings, attention block, FFN, language model head."""

from __future__ import annotations

import random
from dataclasses import dataclass

from toy_transformer.attention import causal_mask, project, scaled_dot_product_attention
from toy_transformer.tensors import (
    Matrix,
    Vector,
    add_mat,
    add_vec,
    apply_row_fn,
    layer_norm,
    matvec,
    rand_mat,
    rand_vec,
    zeros_mat,
)


@dataclass
class FeedForward:
    w1: Matrix
    b1: Vector
    w2: Matrix
    b2: Vector

    @classmethod
    def create(cls, d_model: int, d_ff: int, rng: random.Random) -> "FeedForward":
        return cls(
            w1=rand_mat(d_ff, d_model, rng=rng),
            b1=rand_vec(d_ff, rng=rng),
            w2=rand_mat(d_model, d_ff, rng=rng),
            b2=rand_vec(d_model, rng=rng),
        )

    def __call__(self, x: Matrix) -> Matrix:
        hidden: Matrix = []
        for row in x:
            h = add_vec(matvec(self.w1, row), self.b1)
            h = [max(0.0, v) for v in h]  # ReLU
            hidden.append(h)
        out: Matrix = []
        for row in hidden:
            out.append(add_vec(matvec(self.w2, row), self.b2))
        return out


@dataclass
class CausalSelfAttention:
    w_q: Matrix
    w_k: Matrix
    w_v: Matrix
    w_o: Matrix

    @classmethod
    def create(cls, d_model: int, rng: random.Random) -> "CausalSelfAttention":
        return cls(
            w_q=rand_mat(d_model, d_model, rng=rng),
            w_k=rand_mat(d_model, d_model, rng=rng),
            w_v=rand_mat(d_model, d_model, rng=rng),
            w_o=rand_mat(d_model, d_model, rng=rng),
        )

    def __call__(self, x: Matrix, *, return_weights: bool = False):
        q = project(x, self.w_q)
        k = project(x, self.w_k)
        v = project(x, self.w_v)
        mask = causal_mask(len(x))
        if return_weights:
            attn_out, weights = scaled_dot_product_attention(
                q, k, v, mask=mask, return_weights=True
            )
            out = project(attn_out, self.w_o)
            return out, weights
        attn_out = scaled_dot_product_attention(q, k, v, mask=mask)
        assert not isinstance(attn_out, tuple)
        return project(attn_out, self.w_o)


@dataclass
class DecoderBlock:
    attn: CausalSelfAttention
    ffn: FeedForward

    @classmethod
    def create(cls, d_model: int, d_ff: int, rng: random.Random) -> "DecoderBlock":
        return cls(
            attn=CausalSelfAttention.create(d_model, rng),
            ffn=FeedForward.create(d_model, d_ff, rng),
        )

    def __call__(self, x: Matrix) -> Matrix:
        # Pre-norm style residuals
        a = self.attn(apply_row_fn(x, layer_norm))
        x = add_mat(x, a)
        f = self.ffn(apply_row_fn(x, layer_norm))
        return add_mat(x, f)


@dataclass
class ToyDecoderLM:
    token_emb: Matrix  # [vocab, d]
    pos_emb: Matrix  # [max_seq, d]
    blocks: list[DecoderBlock]
    lm_head: Matrix  # [vocab, d]
    d_model: int
    max_seq: int

    @classmethod
    def create(
        cls,
        *,
        vocab_size: int,
        d_model: int = 16,
        n_layers: int = 2,
        d_ff: int | None = None,
        max_seq: int = 64,
        seed: int = 7,
    ) -> "ToyDecoderLM":
        rng = random.Random(seed)
        d_ff = d_ff or d_model * 4
        return cls(
            token_emb=rand_mat(vocab_size, d_model, rng=rng),
            pos_emb=rand_mat(max_seq, d_model, rng=rng),
            blocks=[DecoderBlock.create(d_model, d_ff, rng) for _ in range(n_layers)],
            lm_head=rand_mat(vocab_size, d_model, rng=rng),
            d_model=d_model,
            max_seq=max_seq,
        )

    def embed(self, token_ids: list[int]) -> Matrix:
        if len(token_ids) > self.max_seq:
            raise ValueError(f"sequence length {len(token_ids)} > max_seq {self.max_seq}")
        xs: Matrix = []
        for pos, tid in enumerate(token_ids):
            te = self.token_emb[tid]
            pe = self.pos_emb[pos]
            xs.append(add_vec(te, pe))
        return xs

    def forward_hidden(self, token_ids: list[int]) -> Matrix:
        x = self.embed(token_ids)
        for block in self.blocks:
            x = block(x)
        return apply_row_fn(x, layer_norm)

    def logits_at_last(self, token_ids: list[int]) -> Vector:
        hidden = self.forward_hidden(token_ids)
        last = hidden[-1]
        # vocab logits = lm_head @ last  (lm_head is [vocab, d])
        return [sum(row[j] * last[j] for j in range(self.d_model)) for row in self.lm_head]

    def attention_weights(self, token_ids: list[int], *, layer: int = 0) -> Matrix:
        """Return causal attention weights from one layer for visualization."""
        x = self.embed(token_ids)
        for i, block in enumerate(self.blocks):
            if i == layer:
                _, weights = block.attn(apply_row_fn(x, layer_norm), return_weights=True)
                return weights
            x = block(x)
        raise IndexError(f"layer {layer} out of range")
