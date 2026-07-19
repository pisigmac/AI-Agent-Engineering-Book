# Chapter 009 — Transformer Architecture

Tiny decoder-only transformer lab (pure Python). Weights are random: use it to learn **shapes and control flow**, not language quality.

## Setup

```bash
cd code/chapter-009
pip install pytest
```

## Run

```bash
pytest -q
python main.py encode "hello agent world"
python main.py attend "hello agent world"
python main.py forward "hello agent"
python main.py generate "hello" --max-new-tokens 5
```

## Layout

| Module | Role |
|--------|------|
| `tokenizer.py` | Tiny whitespace vocab |
| `tensors.py` | matmul/softmax/layer_norm helpers |
| `attention.py` | Causal scaled dot-product attention |
| `blocks.py` | FFN, decoder block, `ToyDecoderLM` |
| `generate.py` | Greedy decode loop |

## Mapping to production

| Toy | Hosted LLM API |
|-----|----------------|
| `encode` | Provider tokenizer |
| `forward` / logits | GPU inference + KV cache |
| `greedy_generate` | `temperature=0` completion |
| causal mask | Built into decoder models |
