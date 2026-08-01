#!/usr/bin/env python3
"""Chapter 25 CLI — advanced RAG / enterprise search."""

from __future__ import annotations

import argparse
import json

from advrag.compress import compress_hits
from advrag.corpus import all_children, build_parent_child_index
from advrag.enterprise import EnterpriseSearch, EnterpriseSearchConfig
from advrag.hybrid import HybridRetriever
from advrag.query_ops import expand_query, multi_queries
from advrag.rerank import SimpleReranker


def cmd_hybrid(args: argparse.Namespace) -> int:
    ret = HybridRetriever()
    ret.index(all_children())
    hits = ret.search(args.query, k=args.k, mode=args.mode)
    print(
        json.dumps(
            {
                "query": args.query,
                "mode": args.mode,
                "hits": [h.to_dict() for h in hits],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_expand(args: argparse.Namespace) -> int:
    print(
        json.dumps(
            {
                "query": args.query,
                "expanded": expand_query(args.query),
                "multi": multi_queries(args.query, n=args.n),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    cfg = EnterpriseSearchConfig(
        mode=args.mode,
        multi_query=not args.no_multi,
        parent_expand=not args.no_parent,
        compress=not args.no_compress,
        rerank=not args.no_rerank,
        final_k=args.k,
    )
    eng = EnterpriseSearch.with_default_corpus(config=cfg)
    where = json.loads(args.where) if args.where else None
    result = eng.search(args.query, filters=where)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    eng = EnterpriseSearch.with_default_corpus()
    modes = ["bm25", "dense", "hybrid"]
    out = {}
    for mode in modes:
        eng.config.mode = mode
        eng.config.multi_query = False
        eng.config.parent_expand = True
        eng.config.compress = False
        eng.config.rerank = True
        r = eng.search(args.query)
        out[mode] = [h.id for h in r.hits[: args.k]]
    # full enterprise
    eng2 = EnterpriseSearch.with_default_corpus()
    full = eng2.search(args.query)
    out["enterprise"] = [h.id for h in full.hits[: args.k]]
    print(json.dumps({"query": args.query, "top_ids": out}, indent=2))
    return 0


def cmd_pipeline_steps(args: argparse.Namespace) -> int:
    """Show intermediate stages for teaching/debug."""
    pci = build_parent_child_index()
    ret = HybridRetriever()
    ret.index(pci.all_indexable())
    variants = multi_queries(args.query, n=3)
    lists = [ret.search(q, k=8, mode="hybrid") for q in variants]
    from advrag.fusion import reciprocal_rank_fusion

    fused = reciprocal_rank_fusion(lists, k=8)
    parents = pci.expand_to_parents(fused, k=6)
    compressed = compress_hits(args.query, parents, max_chars=200)
    final = SimpleReranker().rerank(args.query, compressed, k=args.k)
    print(
        json.dumps(
            {
                "variants": variants,
                "fused": [h.id for h in fused],
                "parents": [h.id for h in parents],
                "compressed_preview": [
                    {"id": h.id, "chars": len(h.text), "text": h.text[:120]} for h in compressed
                ],
                "final": [h.to_dict() for h in final],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 25 — advanced RAG / enterprise search")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_h = sub.add_parser("hybrid", help="BM25 / dense / hybrid search")
    p_h.add_argument("query")
    p_h.add_argument("--mode", choices=["bm25", "dense", "hybrid"], default="hybrid")
    p_h.add_argument("-k", type=int, default=5)

    p_e = sub.add_parser("expand", help="Query expansion / multi-query")
    p_e.add_argument("query")
    p_e.add_argument("-n", type=int, default=3)

    p_s = sub.add_parser("search", help="Full enterprise search pipeline")
    p_s.add_argument("query")
    p_s.add_argument("-k", type=int, default=5)
    p_s.add_argument("--mode", choices=["bm25", "dense", "hybrid"], default="hybrid")
    p_s.add_argument("--where", default=None)
    p_s.add_argument("--no-multi", action="store_true")
    p_s.add_argument("--no-parent", action="store_true")
    p_s.add_argument("--no-compress", action="store_true")
    p_s.add_argument("--no-rerank", action="store_true")

    p_c = sub.add_parser("compare", help="Compare retrieval modes on one query")
    p_c.add_argument("query")
    p_c.add_argument("-k", type=int, default=3)

    p_p = sub.add_parser("steps", help="Show intermediate pipeline stages")
    p_p.add_argument("query")
    p_p.add_argument("-k", type=int, default=3)

    args = parser.parse_args(argv)
    if args.cmd == "hybrid":
        return cmd_hybrid(args)
    if args.cmd == "expand":
        return cmd_expand(args)
    if args.cmd == "search":
        return cmd_search(args)
    if args.cmd == "compare":
        return cmd_compare(args)
    if args.cmd == "steps":
        return cmd_pipeline_steps(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
