#!/usr/bin/env python3
"""Chapter 20 CLI — embedding model catalog, benchmark, recommend."""

from __future__ import annotations

import argparse
import json

from embbench.benchmark import run_benchmark, tradeoff_matrix
from embbench.catalog import default_catalog
from embbench.dataset import corpus_texts, multilingual_pairs
from embbench.recommend import recommend


def cmd_catalog() -> int:
    rows = [c.to_dict() for c in default_catalog()]
    print(json.dumps({"models": rows}, indent=2))
    return 0


def cmd_tradeoffs() -> int:
    print(json.dumps({"tradeoffs": tradeoff_matrix()}, indent=2))
    return 0


def cmd_bench(args: argparse.Namespace) -> int:
    ids = args.models.split(",") if args.models else None
    report = run_benchmark(ids, include_multilingual=not args.english_only)
    print(json.dumps(report.to_dict(), indent=2))
    return 0


def cmd_recommend(args: argparse.Namespace) -> int:
    out = recommend(
        multilingual=args.multilingual,
        prefer_local=args.local,
        max_cost_per_1m=args.max_cost,
        max_dimensions=args.max_dims,
        need_instructions=args.instructions,
    )
    print(json.dumps(out, indent=2))
    return 0


def cmd_corpus() -> int:
    print(
        json.dumps(
            {
                "corpus": corpus_texts(),
                "multilingual_queries": [
                    {"lang": p.lang, "query": p.query, "positive": p.positive}
                    for p in multilingual_pairs()
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 20 — embedding models / benchmark")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("catalog", help="List embedding model cards")
    sub.add_parser("tradeoffs", help="Qualitative trade-off matrix")
    sub.add_parser("corpus", help="Show benchmark corpus and multilingual queries")

    p_b = sub.add_parser("bench", help="Run offline retrieval benchmark")
    p_b.add_argument(
        "--models",
        default=None,
        help="Comma-separated model_ids (default: teaching + local/API proxies)",
    )
    p_b.add_argument("--english-only", action="store_true")

    p_r = sub.add_parser("recommend", help="Constraint-based recommendation")
    p_r.add_argument("--multilingual", action="store_true")
    p_r.add_argument("--local", action="store_true")
    p_r.add_argument("--max-cost", type=float, default=None)
    p_r.add_argument("--max-dims", type=int, default=None)
    p_r.add_argument("--instructions", action="store_true")

    args = parser.parse_args(argv)
    if args.cmd == "catalog":
        return cmd_catalog()
    if args.cmd == "tradeoffs":
        return cmd_tradeoffs()
    if args.cmd == "corpus":
        return cmd_corpus()
    if args.cmd == "bench":
        return cmd_bench(args)
    if args.cmd == "recommend":
        return cmd_recommend(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
