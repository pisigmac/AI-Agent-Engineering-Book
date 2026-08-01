#!/usr/bin/env python3
"""Chapter 24 CLI — production RAG system."""

from __future__ import annotations

import argparse
import json

from ragkit.eval import evaluate_rag
from ragkit.pipeline import RAGConfig, RAGSystem


def _system(args: argparse.Namespace) -> RAGSystem:
    cfg = RAGConfig(
        retrieve_k=args.retrieve_k,
        final_k=args.final_k,
        include_prompt_in_result=args.show_prompt,
    )
    return RAGSystem.with_default_corpus(config=cfg)


def cmd_ask(args: argparse.Namespace) -> int:
    rag = _system(args)
    where = json.loads(args.where) if args.where else None
    ans = rag.ask(args.question, where=where, use_memory=not args.no_memory)
    payload = ans.to_dict()
    if not args.verbose:
        payload.pop("prompt", None)
        payload["retrieved"] = [
            {"id": r["id"], "score": r["score"], "ranker_score": r["ranker_score"]}
            for r in payload["retrieved"]
        ]
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if ans.grounded else 1


def cmd_chat(args: argparse.Namespace) -> int:
    rag = _system(args)
    turns = args.turns or [
        "How do I get a refund?",
        "What about canceling my subscription?",
    ]
    out = []
    for q in turns:
        ans = rag.ask(q)
        out.append(
            {
                "question": q,
                "grounded": ans.grounded,
                "answer": ans.answer.split("Sources:")[0].strip(),
                "citations": [c.doc_id for c in ans.citations],
                "memory_turns": ans.memory_turns,
            }
        )
    print(json.dumps({"turns": out}, indent=2, ensure_ascii=False))
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    rag = RAGSystem.with_default_corpus(
        config=RAGConfig(retrieve_k=args.retrieve_k, final_k=args.final_k)
    )

    def ask(q: str):
        # fresh memory per labeled question
        rag.reset_memory()
        return rag.ask(q, use_memory=False)

    report = evaluate_rag(ask)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    ok = report["citation_hit_rate"] >= args.min_hit_rate
    return 0 if ok else 1


def cmd_retrieve(args: argparse.Namespace) -> int:
    rag = _system(args)
    where = json.loads(args.where) if args.where else None
    raw = rag.retriever.retrieve(args.query, k=args.retrieve_k, where=where)
    ranked = rag.ranker.rank(args.query, raw)[: args.final_k]
    print(
        json.dumps(
            {
                "query": args.query,
                "raw": [c.to_dict() for c in raw],
                "ranked": [c.to_dict() for c in ranked],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 24 — production RAG")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--retrieve-k", type=int, default=8)
        p.add_argument("--final-k", type=int, default=4)

    p_a = sub.add_parser("ask", help="One-shot RAG question")
    add_common(p_a)
    p_a.add_argument("question")
    p_a.add_argument("--where", default=None)
    p_a.add_argument("--no-memory", action="store_true")
    p_a.add_argument("--show-prompt", action="store_true")
    p_a.add_argument("--verbose", action="store_true")

    p_c = sub.add_parser("chat", help="Multi-turn demo with memory")
    add_common(p_c)
    p_c.add_argument("--turns", nargs="*", default=None)

    p_e = sub.add_parser("eval", help="Run labeled citation hit-rate eval")
    add_common(p_e)
    p_e.add_argument("--min-hit-rate", type=float, default=0.8)

    p_r = sub.add_parser("retrieve", help="Show retrieve + rank only")
    add_common(p_r)
    p_r.add_argument("query")
    p_r.add_argument("--where", default=None)

    args = parser.parse_args(argv)
    if args.cmd == "ask":
        return cmd_ask(args)
    if args.cmd == "chat":
        return cmd_chat(args)
    if args.cmd == "eval":
        return cmd_eval(args)
    if args.cmd == "retrieve":
        return cmd_retrieve(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
