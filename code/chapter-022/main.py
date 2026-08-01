#!/usr/bin/env python3
"""Chapter 22 CLI — FAISS indexes and PDF search."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from faisskit.optimize import compare_kinds, sweep_nprobe
from faisskit.pdf_search import PdfSearchEngine, build_sample_pdfs
from faisskit.persist import load_service, save_service
from faisskit.service import FaissIndexService


def _sample_docs() -> list[dict]:
    return [
        {"id": "refund", "text": "Refund policy money back reverse charge within 30 days", "metadata": {"topic": "billing"}},
        {"id": "ship", "text": "Shipping tracking express delivery 5 to 7 business days", "metadata": {"topic": "logistics"}},
        {"id": "auth", "text": "Password reset two-factor authentication login security", "metadata": {"topic": "security"}},
        {"id": "api", "text": "API rate limits HTTP 429 backoff retry per minute", "metadata": {"topic": "developers"}},
        {"id": "sso", "text": "Enterprise SAML OIDC single sign-on groups roles", "metadata": {"topic": "security"}},
        {"id": "privacy", "text": "Privacy export delete personal data confidential", "metadata": {"topic": "legal"}},
    ]


def cmd_index_demo(args: argparse.Namespace) -> int:
    svc = FaissIndexService(kind=args.kind, dimensions=64, nlist=4, nprobe=2)
    svc.add_documents(_sample_docs())
    r = svc.search(args.query, k=args.k, where=json.loads(args.where) if args.where else None)
    print(json.dumps({"stats": svc.stats().to_dict(), "result": r.to_dict()}, indent=2))
    return 0


def cmd_compare() -> int:
    docs = _sample_docs()
    queries = [
        "money back refund",
        "package tracking shipping",
        "forgot password",
        "HTTP 429",
    ]
    print(json.dumps(compare_kinds(docs, queries, dimensions=64, k=3), indent=2))
    return 0


def cmd_nprobe() -> int:
    docs = _sample_docs() * 3  # a bit more mass for IVF
    # unique ids
    for i, d in enumerate(docs):
        d = dict(d)
        d["id"] = f"{d['id']}_{i}"
        docs[i] = d
    svc = FaissIndexService(kind="ivf_flat", dimensions=64, nlist=4, nprobe=1)
    svc.add_documents(docs)
    rows = sweep_nprobe(svc, ["refund money", "shipping tracking", "password"], nprobes=[1, 2, 4])
    print(json.dumps({"sweep": rows}, indent=2))
    return 0


def cmd_persist(args: argparse.Namespace) -> int:
    path = Path(args.path)
    svc = FaissIndexService(kind=args.kind, dimensions=64, nlist=4, nprobe=2)
    svc.add_documents(_sample_docs())
    save_service(svc, path)
    svc2 = load_service(path)
    r = svc2.search("money back", k=2)
    print(
        json.dumps(
            {
                "saved": str(path),
                "ntotal": svc2.ntotal,
                "hits": [h.to_dict() for h in r.hits],
            },
            indent=2,
        )
    )
    return 0


def cmd_pdf_search(args: argparse.Namespace) -> int:
    if args.pdfs:
        paths = [Path(p) for p in args.pdfs]
    else:
        out = Path(args.fixture_dir or tempfile.mkdtemp(prefix="faiss-pdfs-"))
        paths = build_sample_pdfs(out)
    engine = PdfSearchEngine.from_pdfs(
        paths, kind=args.kind, dimensions=64, max_chars=args.chunk
    )
    r = engine.search(args.query, k=args.k, source=args.source)
    print(
        json.dumps(
            {
                "sources": engine.sources,
                "stats": engine.service.stats().to_dict(),
                "result": r.to_dict(),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_build_fixtures(args: argparse.Namespace) -> int:
    paths = build_sample_pdfs(args.dir)
    print(json.dumps({"pdfs": [str(p) for p in paths]}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 22 — FAISS + PDF search")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_i = sub.add_parser("search", help="Index sample docs and search")
    p_i.add_argument("query", nargs="?", default="money back refund")
    p_i.add_argument("--kind", default="flat_ip", choices=["flat_ip", "flat_l2", "ivf_flat", "hnsw"])
    p_i.add_argument("-k", type=int, default=3)
    p_i.add_argument("--where", default=None)

    sub.add_parser("compare", help="Compare flat / IVF / HNSW")
    sub.add_parser("nprobe", help="IVF nprobe latency sweep")

    p_p = sub.add_parser("persist", help="Save/load FAISS index + sidecar")
    p_p.add_argument("--path", default="/tmp/faisskit-index")
    p_p.add_argument("--kind", default="hnsw")

    p_pdf = sub.add_parser("pdf-search", help="PDF search project")
    p_pdf.add_argument("query", nargs="?", default="How do I get a refund?")
    p_pdf.add_argument("--pdfs", nargs="*", default=None)
    p_pdf.add_argument("--fixture-dir", default=None)
    p_pdf.add_argument("--kind", default="flat_ip")
    p_pdf.add_argument("-k", type=int, default=3)
    p_pdf.add_argument("--chunk", type=int, default=350)
    p_pdf.add_argument("--source", default=None)

    p_f = sub.add_parser("fixtures", help="Write sample PDFs")
    p_f.add_argument("--dir", default="code/chapter-022/fixtures/pdfs")

    args = parser.parse_args(argv)
    if args.cmd == "search":
        return cmd_index_demo(args)
    if args.cmd == "compare":
        return cmd_compare()
    if args.cmd == "nprobe":
        return cmd_nprobe()
    if args.cmd == "persist":
        return cmd_persist(args)
    if args.cmd == "pdf-search":
        return cmd_pdf_search(args)
    if args.cmd == "fixtures":
        return cmd_build_fixtures(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
