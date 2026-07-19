"""Tests for Chapter 9 toy transformer."""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from toy_transformer.attention import NEG_INF, causal_mask, scaled_dot_product_attention
from toy_transformer.blocks import ToyDecoderLM
from toy_transformer.generate import greedy_generate
from toy_transformer.tensors import softmax
from toy_transformer.tokenizer import TinyTokenizer


def test_tokenizer_roundtrip_known_words():
    tok = TinyTokenizer.default()
    ids = tok.encode("hello agent world", add_bos=True)
    assert tok.bos_id in ids
    assert tok.decode(ids) == "hello agent world"


def test_tokenizer_unknown():
    tok = TinyTokenizer.default()
    ids = tok.encode("hello zzzx", add_bos=False)
    assert tok.unk_id in ids


def test_causal_mask_blocks_future():
    mask = causal_mask(4)
    for i in range(4):
        for j in range(4):
            if j > i:
                assert mask[i][j] == NEG_INF
            else:
                assert mask[i][j] == 0.0


def test_attention_weights_respect_mask():
    # identity-ish q,k so scores are high on diagonals; mask still zeros future
    q = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
    k = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
    v = [[1.0, 0.0], [2.0, 0.0], [3.0, 0.0]]
    mask = causal_mask(3)
    _, weights = scaled_dot_product_attention(q, k, v, mask=mask, return_weights=True)
    for i in range(3):
        for j in range(3):
            if j > i:
                assert weights[i][j] < 1e-6
        assert abs(sum(weights[i]) - 1.0) < 1e-5


def test_softmax_stable():
    s = softmax([1000.0, 1000.0, 1000.0])
    assert abs(sum(s) - 1.0) < 1e-9
    assert all(math.isfinite(x) for x in s)


def test_forward_logits_shape():
    tok = TinyTokenizer.default()
    model = ToyDecoderLM.create(vocab_size=tok.vocab_size, d_model=8, n_layers=1, seed=1)
    ids = tok.encode("hello agent")
    logits = model.logits_at_last(ids)
    assert len(logits) == tok.vocab_size
    assert all(math.isfinite(x) for x in logits)


def test_greedy_generate_respects_max_new_tokens():
    tok = TinyTokenizer.default()
    model = ToyDecoderLM.create(vocab_size=tok.vocab_size, d_model=8, n_layers=1, seed=2)
    prompt_ids = tok.encode("hello", add_bos=True)
    result = greedy_generate(model, tok, "hello", max_new_tokens=3)
    # at most prompt + 3 new tokens
    assert len(result.token_ids) <= len(prompt_ids) + 3
    assert len(result.steps) <= 3


def test_model_attention_weights_causal():
    tok = TinyTokenizer.default()
    model = ToyDecoderLM.create(vocab_size=tok.vocab_size, d_model=8, n_layers=2, seed=3)
    ids = tok.encode("hello agent world")
    w = model.attention_weights(ids, layer=0)
    n = len(ids)
    assert len(w) == n and len(w[0]) == n
    for i in range(n):
        for j in range(i + 1, n):
            assert w[i][j] < 1e-6
