"""Greedy decoding loop for the toy LM."""

from __future__ import annotations

from dataclasses import dataclass

from toy_transformer.blocks import ToyDecoderLM
from toy_transformer.tensors import argmax
from toy_transformer.tokenizer import TinyTokenizer


@dataclass
class GenerateResult:
    token_ids: list[int]
    text: str
    steps: list[dict[str, object]]


def greedy_generate(
    model: ToyDecoderLM,
    tokenizer: TinyTokenizer,
    prompt: str,
    *,
    max_new_tokens: int = 8,
) -> GenerateResult:
    ids = tokenizer.encode(prompt, add_bos=True, add_eos=False)
    steps: list[dict[str, object]] = []
    for step in range(max_new_tokens):
        logits = model.logits_at_last(ids)
        next_id = argmax(logits)
        steps.append(
            {
                "step": step,
                "next_id": next_id,
                "next_token": tokenizer.id_to_token[next_id],
                "context_len": len(ids),
            }
        )
        ids.append(next_id)
        if next_id == tokenizer.eos_id:
            break
    return GenerateResult(token_ids=ids, text=tokenizer.decode(ids), steps=steps)
