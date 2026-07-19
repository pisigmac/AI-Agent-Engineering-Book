"""Chapter 9 CLI — toy transformer lab."""

from __future__ import annotations

import argparse
import json

from toy_transformer.attention import causal_mask
from toy_transformer.blocks import ToyDecoderLM
from toy_transformer.generate import greedy_generate
from toy_transformer.tokenizer import TinyTokenizer


def _model(tokenizer: TinyTokenizer) -> ToyDecoderLM:
    return ToyDecoderLM.create(vocab_size=tokenizer.vocab_size, d_model=16, n_layers=2, seed=7)


def cmd_encode(text: str) -> int:
    tok = TinyTokenizer.default()
    ids = tok.encode(text)
    print(
        json.dumps(
            {
                "text": text,
                "ids": ids,
                "tokens": [tok.id_to_token[i] for i in ids],
                "decoded": tok.decode(ids),
            },
            indent=2,
        )
    )
    return 0


def cmd_attend(text: str) -> int:
    tok = TinyTokenizer.default()
    model = _model(tok)
    ids = tok.encode(text)
    weights = model.attention_weights(ids, layer=0)
    # Round for readability
    pretty = [[round(v, 4) for v in row] for row in weights]
    mask = causal_mask(len(ids))
    future_ok = all(mask[i][j] < 0 for i in range(len(ids)) for j in range(i + 1, len(ids)))
    print(
        json.dumps(
            {
                "ids": ids,
                "tokens": [tok.id_to_token[i] for i in ids],
                "attention_weights_layer0": pretty,
                "causal_mask_blocks_future": future_ok,
            },
            indent=2,
        )
    )
    return 0


def cmd_generate(prompt: str, max_new_tokens: int) -> int:
    tok = TinyTokenizer.default()
    model = _model(tok)
    result = greedy_generate(model, tok, prompt, max_new_tokens=max_new_tokens)
    print(
        json.dumps(
            {
                "prompt": prompt,
                "output_text": result.text,
                "token_ids": result.token_ids,
                "steps": result.steps,
                "note": "Toy random weights — text is not meaningful; inspect the loop.",
            },
            indent=2,
        )
    )
    return 0


def cmd_forward(text: str) -> int:
    tok = TinyTokenizer.default()
    model = _model(tok)
    ids = tok.encode(text)
    logits = model.logits_at_last(ids)
    top = sorted(range(len(logits)), key=lambda i: logits[i], reverse=True)[:5]
    print(
        json.dumps(
            {
                "ids": ids,
                "logits_len": len(logits),
                "top5": [
                    {"id": i, "token": tok.id_to_token[i], "logit": round(logits[i], 4)}
                    for i in top
                ],
            },
            indent=2,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 9 — toy transformer lab")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_enc = sub.add_parser("encode", help="Tokenize text")
    p_enc.add_argument("text")

    p_att = sub.add_parser("attend", help="Show causal attention weights")
    p_att.add_argument("text", nargs="?", default="hello agent world")

    p_gen = sub.add_parser("generate", help="Greedy generate with toy weights")
    p_gen.add_argument("prompt", nargs="?", default="hello")
    p_gen.add_argument("--max-new-tokens", type=int, default=5)

    p_fwd = sub.add_parser("forward", help="Logits at last position")
    p_fwd.add_argument("text", nargs="?", default="hello agent")

    args = parser.parse_args(argv)
    if args.cmd == "encode":
        return cmd_encode(args.text)
    if args.cmd == "attend":
        return cmd_attend(args.text)
    if args.cmd == "generate":
        return cmd_generate(args.prompt, args.max_new_tokens)
    if args.cmd == "forward":
        return cmd_forward(args.text)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
