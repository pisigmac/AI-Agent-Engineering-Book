#!/usr/bin/env python3
"""Chapter 18 CLI — semantic search engine."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from searchkit.corpus import knowledge_base
from searchkit.engine import SearchEngine
from searchkit.persist import load_engine, save_engine
from searchkit.types import Document


def _engine_from_args(args: argparse.Namespace) -> SearchEngine:
    if getattr(args, "index", None) and Path(args.index).exists():
        return load_engine(args.index)
    return SearchEngine.with_defaults()


def cmd_stats(args: argparse.Namespace) -> int:
    eng = _engine_from_args(args)
    print(json.dumps(eng.stats(), indent=2))
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    eng = _engine_from_args(args)
    filters = {}
    if args.topic:
        filters["topic"] = args.topic
    if args.product:
        filters["product"] = args.product
    boosts = None
    if args.strategy == "boost":
        boosts = {"topic": {"billing": 1.2, "developers": 1.1}}
    resp = eng.search(
        args.query,
        k=args.k,
        min_score=args.min_score,
        filters=filters or None,
        strategy=args.strategy,
        mmr_lambda=args.mmr_lambda,
        boosts=boosts,
    )
    print(json.dumps(resp.to_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_explain(args: argparse.Namespace) -> int:
    eng = _engine_from_args(args)
    print(json.dumps(eng.explain(args.query, args.doc_id), indent=2, ensure_ascii=False))
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    eng = _engine_from_args(args)
    report = eng.evaluate_default(k=args.k)
    print(json.dumps(report.to_dict(), indent=2))
    return 0 if report.recall_at_k >= args.min_recall else 1


def cmd_ingest(args: argparse.Namespace) -> int:
    eng = SearchEngine()
    docs = knowledge_base()
    if args.file:
        data = json.loads(Path(args.file).read_text(encoding="utf-8"))
        docs = [
            Document(
                id=d["id"],
                text=d["text"],
                title=d.get("title", ""),
                metadata=d.get("metadata", {}),
            )
            for d in data
        ]
    n = eng.ingest(docs, rebuild=True)
    if args.out:
        save_engine(eng, args.out)
    print(json.dumps({"ingested": n, "stats": eng.stats(), "saved": args.out}, indent=2))
    return 0


def cmd_demo() -> int:
    eng = SearchEngine.with_defaults()
    queries = [
        "How do I reverse a charge?",
        "SAML login for enterprise",
        "429 too many requests",
    ]
    out = []
    for q in queries:
        r = eng.search(q, k=3)
        out.append(
            {
                "query": q,
                "top": [{"id": h.id, "score": round(h.score, 4), "title": h.title} for h in r.hits],
            }
        )
    report = eng.evaluate_default(k=3)
    print(json.dumps({"demo": out, "eval": report.to_dict()}, indent=2, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 18 — semantic search engine")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_index(p: argparse.ArgumentParser) -> None:
        p.add_argument("--index", default=None, help="Path to saved engine JSON")

    p_stats = sub.add_parser("stats", help="Index statistics")
    add_index(p_stats)

    p_s = sub.add_parser("search", help="Semantic search")
    add_index(p_s)
    p_s.add_argument("query")
    p_s.add_argument("-k", type=int, default=5)
    p_s.add_argument("--min-score", type=float, default=None)
    p_s.add_argument("--topic", default=None)
    p_s.add_argument("--product", default=None)
    p_s.add_argument("--strategy", choices=["cosine", "mmr", "boost"], default="cosine")
    p_s.add_argument("--mmr-lambda", type=float, default=0.7)

    p_e = sub.add_parser("explain", help="Explain query vs document score")
    add_index(p_e)
    p_e.add_argument("query")
    p_e.add_argument("doc_id")

    p_ev = sub.add_parser("eval", help="Run labeled retrieval eval")
    add_index(p_ev)
    p_ev.add_argument("-k", type=int, default=3)
    p_ev.add_argument("--min-recall", type=float, default=0.0)

    p_i = sub.add_parser("ingest", help="Build index from corpus or JSON file")
    p_i.add_argument("--file", default=None, help="JSON list of documents")
    p_i.add_argument("--out", default=None, help="Save engine snapshot path")

    sub.add_parser("demo", help="Demo queries + eval summary")

    args = parser.parse_args(argv)
    if args.cmd == "stats":
        return cmd_stats(args)
    if args.cmd == "search":
        return cmd_search(args)
    if args.cmd == "explain":
        return cmd_explain(args)
    if args.cmd == "eval":
        return cmd_eval(args)
    if args.cmd == "ingest":
        return cmd_ingest(args)
    if args.cmd == "demo":
        return cmd_demo()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
