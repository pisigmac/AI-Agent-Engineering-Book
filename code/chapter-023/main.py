#!/usr/bin/env python3
"""Chapter 23 CLI — Chroma collections and knowledge assistant."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from chromakit.assistant import KnowledgeAssistant
from chromakit.corpus import knowledge_docs
from chromakit.store import ChromaStore


def cmd_ingest(args: argparse.Namespace) -> int:
    store = ChromaStore("knowledge_base", path=args.path, dimensions=args.dims)
    n = store.upsert_docs(knowledge_docs())
    print(json.dumps({"upserted": n, "stats": store.stats()}, indent=2))
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    store = ChromaStore("knowledge_base", path=args.path, dimensions=args.dims)
    if store.count() == 0:
        store.upsert_docs(knowledge_docs())
    where = json.loads(args.where) if args.where else None
    result = store.query(args.query, n_results=args.k, where=where)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_ask(args: argparse.Namespace) -> int:
    assistant = KnowledgeAssistant(path=args.path, dimensions=args.dims)
    if assistant.store.count() == 0:
        assistant.ingest_default()
    where = json.loads(args.where) if args.where else None
    ans = assistant.ask(args.question, n_results=args.k, where=where)
    print(json.dumps(ans.to_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    store = ChromaStore("knowledge_base", path=args.path, dimensions=args.dims)
    print(
        json.dumps(
            {
                "stats": store.stats(),
                "collections": store.list_collections(),
            },
            indent=2,
        )
    )
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    path = args.path
    assistant = KnowledgeAssistant(path=path, dimensions=64)
    assistant.ingest_default()
    questions = [
        "How do I get my money back?",
        "Where is my package tracking number?",
        "I forgot my password",
        "What does HTTP 429 mean?",
    ]
    out = []
    for q in questions:
        ans = assistant.ask(q, n_results=2)
        out.append(
            {
                "question": q,
                "grounded": ans.grounded,
                "answer": ans.answer[:200],
                "citations": [c["id"] for c in ans.citations],
            }
        )
    # filtered ask
    filtered = assistant.ask("security login", n_results=2, where={"topic": "security"})
    print(
        json.dumps(
            {
                "backend": assistant.store.backend,
                "count": assistant.store.count(),
                "qa": out,
                "filtered_security": filtered.to_dict(),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 23 — Chroma knowledge assistant")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--path",
            default=None,
            help="Persistent directory (default: ephemeral in-memory)",
        )
        p.add_argument("--dims", type=int, default=64)

    p_i = sub.add_parser("ingest", help="Load sample knowledge base")
    add_common(p_i)

    p_q = sub.add_parser("query", help="Raw vector query")
    add_common(p_q)
    p_q.add_argument("query")
    p_q.add_argument("-k", type=int, default=3)
    p_q.add_argument("--where", default=None, help='JSON filter e.g. {"topic":"billing"}')

    p_a = sub.add_parser("ask", help="Knowledge assistant Q&A with citations")
    add_common(p_a)
    p_a.add_argument("question")
    p_a.add_argument("-k", type=int, default=3)
    p_a.add_argument("--where", default=None)

    p_s = sub.add_parser("stats", help="Collection stats")
    add_common(p_s)

    p_d = sub.add_parser("demo", help="Ingest + multi-question demo")
    add_common(p_d)

    args = parser.parse_args(argv)
    if args.cmd == "ingest":
        return cmd_ingest(args)
    if args.cmd == "query":
        return cmd_query(args)
    if args.cmd == "ask":
        return cmd_ask(args)
    if args.cmd == "stats":
        return cmd_stats(args)
    if args.cmd == "demo":
        return cmd_demo(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
