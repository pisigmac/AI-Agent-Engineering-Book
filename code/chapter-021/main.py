#!/usr/bin/env python3
"""Chapter 21 CLI — mini vector database."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from vectordb.compare import compare_indexes
from vectordb.database import VectorDB
from vectordb.demo_data import DOCS, QUERIES
from vectordb.persist import load_db, save_db


def _seed(db: VectorDB, name: str, index_type: str, **kwargs: object) -> None:
    col = db.create_collection(name, index_type=index_type, exist_ok=True, **kwargs)  # type: ignore[arg-type]
    if len(col) == 0:
        col.upsert_many(DOCS)
        if index_type == "ivf":
            col.rebuild()


def cmd_demo() -> int:
    db = VectorDB()
    _seed(db, "kb", "flat")
    results = []
    col = db.get_collection("kb")
    for q in QUERIES:
        r = col.query(text=q, k=3)
        results.append(
            {
                "query": q,
                "hits": [{"id": h.id, "score": round(h.score, 4)} for h in r.hits],
                "scanned": r.n_scanned,
            }
        )
    # tenant filter
    filtered = col.query(text="SSO security", k=5, where={"tenant": "globex"})
    print(
        json.dumps(
            {
                "stats": db.stats(),
                "searches": results,
                "tenant_globex": filtered.to_dict(),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    if args.db and Path(args.db).exists():
        db = load_db(args.db)
    else:
        db = VectorDB()
        _seed(db, args.collection, args.index)
    col = db.get_collection(args.collection)
    where = json.loads(args.where) if args.where else None
    r = col.query(text=args.query, k=args.k, where=where, min_score=args.min_score)
    print(json.dumps(r.to_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_compare() -> int:
    print(json.dumps(compare_indexes(DOCS, QUERIES, k=3, nlist=4, nprobe=2), indent=2))
    return 0


def cmd_persist(args: argparse.Namespace) -> int:
    db = VectorDB()
    _seed(db, "kb_flat", "flat")
    _seed(db, "kb_ivf", "ivf", nlist=4, nprobe=2)
    save_db(db, args.path)
    db2 = load_db(args.path)
    print(
        json.dumps(
            {
                "saved": str(args.path),
                "collections": db2.list_collections(),
                "stats": db2.stats(),
            },
            indent=2,
        )
    )
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    if args.db and Path(args.db).exists():
        db = load_db(args.db)
    else:
        db = VectorDB()
        _seed(db, "kb", "flat")
    print(json.dumps(db.stats(), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 21 — mini vector database")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("demo", help="Seed KB and run sample queries + filter")
    sub.add_parser("compare", help="Compare flat vs IVF scan counts")

    p_q = sub.add_parser("query", help="Query a collection")
    p_q.add_argument("query")
    p_q.add_argument("--collection", default="kb")
    p_q.add_argument("--index", choices=["flat", "ivf"], default="flat")
    p_q.add_argument("-k", type=int, default=5)
    p_q.add_argument("--min-score", type=float, default=None)
    p_q.add_argument("--where", default=None, help='JSON filter e.g. {"topic":"billing"}')
    p_q.add_argument("--db", default=None, help="Path to saved DB JSON")

    p_p = sub.add_parser("persist", help="Save demo DB to JSON and reload")
    p_p.add_argument("--path", default="/tmp/vectordb-demo.json")

    p_s = sub.add_parser("stats", help="Collection stats")
    p_s.add_argument("--db", default=None)

    args = parser.parse_args(argv)
    if args.cmd == "demo":
        return cmd_demo()
    if args.cmd == "compare":
        return cmd_compare()
    if args.cmd == "query":
        return cmd_query(args)
    if args.cmd == "persist":
        return cmd_persist(args)
    if args.cmd == "stats":
        return cmd_stats(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
