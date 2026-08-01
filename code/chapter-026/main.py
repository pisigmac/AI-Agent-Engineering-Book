#!/usr/bin/env python3
"""Chapter 26 CLI — hybrid retriever evaluation."""
from __future__ import annotations
import argparse, json
from hybridret import HybridRetriever

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Chapter 26 — hybrid search")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("--mode", default="hybrid_rrf")
    s.add_argument("-k", type=int, default=5)
    sub.add_parser("compare").add_argument("query")
    sub.add_parser("eval").add_argument("-k", type=int, default=3)
    a = p.parse_args(argv)
    r = HybridRetriever(); r.index()
    if a.cmd == "search":
        print(json.dumps({"query": a.query, "mode": a.mode, "hits": [h.to_dict() for h in r.search(a.query, k=a.k, mode=a.mode)]}, indent=2))
        return 0
    if a.cmd == "compare":
        print(json.dumps(r.compare(a.query), indent=2)); return 0
    print(json.dumps(r.eval_modes(k=a.k), indent=2)); return 0

if __name__ == "__main__":
    raise SystemExit(main())
