#!/usr/bin/env python3
"""Chapter 17 CLI — cost & performance control plane."""

from __future__ import annotations

import argparse
import json

from costkit.batch import Batcher
from costkit.budget import BudgetExceeded
from costkit.compress import compress_text
from costkit.engine import CompleteRequest, CostEngine, MockModel
from costkit.pricing import PriceBook
from costkit.stream import consume_stream, iter_mock_stream
from costkit.types import Budget, TokenUsage


def cmd_prices() -> int:
    book = PriceBook()
    rows = []
    for mid in book.list_models():
        p = book.get(mid)
        rows.append(
            {
                "model_id": p.model_id,
                "input_per_mtok": p.input_per_mtok,
                "output_per_mtok": p.output_per_mtok,
                "notes": p.notes,
            }
        )
    print(json.dumps({"prices": rows}, indent=2))
    return 0


def cmd_complete(args: argparse.Namespace) -> int:
    engine = CostEngine(model=MockModel(fail_times=args.fail_times))
    if args.budget is not None:
        engine.set_budget(Budget(max_cost_usd=args.budget, max_calls=args.max_calls))
    elif args.max_calls is not None:
        engine.set_budget(Budget(max_calls=args.max_calls))

    try:
        for i in range(args.repeat):
            resp = engine.complete(
                CompleteRequest(
                    prompt=args.prompt,
                    model_id=args.model,
                    temperature=0.0 if args.cache else 0.7,
                    use_cache=args.cache,
                    compress=args.compress,
                    max_prompt_chars=args.max_chars,
                )
            )
            if args.repeat == 1:
                print(json.dumps(resp.to_dict(), indent=2, ensure_ascii=False))
            else:
                print(
                    json.dumps(
                        {
                            "i": i,
                            "from_cache": resp.from_cache,
                            "cost_usd": resp.event.cost_usd,
                            "model_id": resp.event.model_id,
                        },
                        ensure_ascii=False,
                    )
                )
    except BudgetExceeded as exc:
        print(json.dumps({"ok": False, "error": "budget_exceeded", "status": exc.status.to_dict()}, indent=2))
        return 1

    if args.repeat > 1 or args.dashboard:
        print(json.dumps({"dashboard": engine.dashboard().to_dict()}, indent=2))
    return 0


def cmd_dashboard_demo() -> int:
    engine = CostEngine()
    engine.set_budget(Budget(max_cost_usd=1.0, max_calls=50))
    prompts = [
        "Classify intent: billing",
        "Classify intent: billing",  # cache hit
        "Summarize the quarterly report with details " * 5,
        "Write a long essay about agents " * 3,
        "Classify intent: shipping",
        "Classify intent: billing",
    ]
    models = [
        "google:gemini-flash",
        "google:gemini-flash",
        "openai:gpt-flagship",
        "openai:gpt-flagship",
        "mistral:small",
        "google:gemini-flash",
    ]
    for p, m in zip(prompts, models):
        engine.complete(
            CompleteRequest(prompt=p, model_id=m, use_cache=True, temperature=0.0, compress=True, max_prompt_chars=400)
        )
    print(json.dumps(engine.dashboard().to_dict(), indent=2))
    return 0


def cmd_compress(text: str, max_chars: int | None) -> int:
    r = compress_text(text, max_chars=max_chars)
    print(json.dumps(r.to_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_batch() -> int:
    def embed_batch(items: list[str]) -> list[int]:
        return [len(x) for x in items]

    b = Batcher(embed_batch, max_size=3)
    texts = [f"doc-{i}" for i in range(7)]
    out = b.map_all(texts)
    print(json.dumps({"results": out, "stats": b.stats.to_dict()}, indent=2))
    return 0


def cmd_stream(prompt: str, model: str) -> int:
    book = PriceBook()
    full = f"[{model}] streamed answer to: {prompt}"
    acc = consume_stream(iter_mock_stream(full, chunk_chars=10), model_id=model, input_tokens=20)
    text, tin, tout = acc.finalize()
    cost = book.cost(model, TokenUsage(tin, tout))
    print(
        json.dumps(
            {
                "text": text,
                "chunks": acc.chunks,
                "input_tokens": tin,
                "output_tokens": tout,
                "cost_usd": cost,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_estimate(model: str, input_tokens: int, output_tokens: int) -> int:
    book = PriceBook()
    usage = TokenUsage(input_tokens, output_tokens)
    print(
        json.dumps(
            {
                "model_id": model,
                "usage": {"input": input_tokens, "output": output_tokens},
                "cost_usd": book.cost(model, usage),
                "price": {
                    "input_per_mtok": book.get(model).input_per_mtok,
                    "output_per_mtok": book.get(model).output_per_mtok,
                },
            },
            indent=2,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 17 — cost & performance")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("prices", help="List illustrative prices")

    p_c = sub.add_parser("complete", help="Cost-aware mock completion")
    p_c.add_argument("prompt")
    p_c.add_argument("--model", default="google:gemini-flash")
    p_c.add_argument("--repeat", type=int, default=1)
    p_c.add_argument("--cache", action=argparse.BooleanOptionalAction, default=True)
    p_c.add_argument("--compress", action="store_true")
    p_c.add_argument("--max-chars", type=int, default=None)
    p_c.add_argument("--budget", type=float, default=None, help="Max USD")
    p_c.add_argument("--max-calls", type=int, default=None)
    p_c.add_argument("--fail-times", type=int, default=0, help="Transient failures before success")
    p_c.add_argument("--dashboard", action="store_true")

    sub.add_parser("dashboard", help="Run a multi-call demo and print dashboard")

    p_z = sub.add_parser("compress", help="Compress prompt text")
    p_z.add_argument("text")
    p_z.add_argument("--max-chars", type=int, default=None)

    sub.add_parser("batch", help="Demo embed-style batching")

    p_s = sub.add_parser("stream", help="Mock streaming usage accounting")
    p_s.add_argument("prompt")
    p_s.add_argument("--model", default="mistral:small")

    p_e = sub.add_parser("estimate", help="Estimate cost for token counts")
    p_e.add_argument("--model", default="openai:gpt-balanced")
    p_e.add_argument("--input", type=int, default=1000)
    p_e.add_argument("--output", type=int, default=500)

    args = parser.parse_args(argv)
    if args.cmd == "prices":
        return cmd_prices()
    if args.cmd == "complete":
        return cmd_complete(args)
    if args.cmd == "dashboard":
        return cmd_dashboard_demo()
    if args.cmd == "compress":
        return cmd_compress(args.text, args.max_chars)
    if args.cmd == "batch":
        return cmd_batch()
    if args.cmd == "stream":
        return cmd_stream(args.prompt, args.model)
    if args.cmd == "estimate":
        return cmd_estimate(args.model, args.input, args.output)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
