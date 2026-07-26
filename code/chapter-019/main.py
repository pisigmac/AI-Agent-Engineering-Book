#!/usr/bin/env python3
"""Chapter 19 CLI — chunking strategies + visualizer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from chunkkit.pipeline import chunk_document, compare_strategies
from chunkkit.sample_docs import sample_handbook, sample_short
from chunkkit.types import SourceDocument
from chunkkit.visualize import boundary_map, visualize_report


def _load_doc(args: argparse.Namespace) -> SourceDocument:
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
        return SourceDocument(id=args.doc_id, text=text, title=Path(args.file).name)
    if args.sample == "short":
        return sample_short()
    return sample_handbook()


def cmd_chunk(args: argparse.Namespace) -> int:
    doc = _load_doc(args)
    kwargs: dict = {}
    if args.strategy == "fixed":
        kwargs = {"size": args.size, "overlap": args.overlap}
    elif args.strategy == "sliding":
        kwargs = {"window": args.size, "stride": args.stride or max(1, args.size // 2)}
    elif args.strategy == "recursive":
        kwargs = {"chunk_size": args.size, "chunk_overlap": args.overlap}
    elif args.strategy == "semantic":
        kwargs = {
            "max_chunk_chars": args.size,
            "similarity_threshold": args.threshold,
        }
    elif args.strategy == "hierarchical":
        kwargs = {
            "parent_size": args.parent_size,
            "child_size": args.size,
            "child_overlap": args.overlap,
        }
    rep = chunk_document(doc, args.strategy, **kwargs)
    if args.format == "json":
        print(json.dumps(rep.to_dict(include_text=not args.no_text), indent=2, ensure_ascii=False))
    else:
        print(visualize_report(rep, doc.text, max_chunks=args.max_show))
        print(boundary_map(doc.text, rep.chunks))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    doc = _load_doc(args)
    rep = compare_strategies(doc, size=args.size)
    print(json.dumps(rep.to_dict(), indent=2))
    return 0


def cmd_visualize(args: argparse.Namespace) -> int:
    args.strategy = args.strategy or "recursive"
    args.format = "text"
    return cmd_chunk(args)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 19 — chunking / visualizer")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_doc_opts(p: argparse.ArgumentParser) -> None:
        p.add_argument("--file", default=None, help="Path to a text/markdown file")
        p.add_argument("--sample", choices=["handbook", "short"], default="handbook")
        p.add_argument("--doc-id", default="doc-1")

    p_c = sub.add_parser("chunk", help="Chunk a document with one strategy")
    add_doc_opts(p_c)
    p_c.add_argument(
        "--strategy",
        choices=["fixed", "sliding", "recursive", "semantic", "hierarchical"],
        default="recursive",
    )
    p_c.add_argument("--size", type=int, default=400)
    p_c.add_argument("--overlap", type=int, default=40)
    p_c.add_argument("--stride", type=int, default=None)
    p_c.add_argument("--threshold", type=float, default=0.25)
    p_c.add_argument("--parent-size", type=int, default=800)
    p_c.add_argument("--format", choices=["text", "json"], default="text")
    p_c.add_argument("--no-text", action="store_true")
    p_c.add_argument("--max-show", type=int, default=20)

    p_v = sub.add_parser("visualize", help="Alias for chunk --format text")
    add_doc_opts(p_v)
    p_v.add_argument(
        "--strategy",
        choices=["fixed", "sliding", "recursive", "semantic", "hierarchical"],
        default="recursive",
    )
    p_v.add_argument("--size", type=int, default=400)
    p_v.add_argument("--overlap", type=int, default=40)
    p_v.add_argument("--stride", type=int, default=None)
    p_v.add_argument("--threshold", type=float, default=0.25)
    p_v.add_argument("--parent-size", type=int, default=800)
    p_v.add_argument("--max-show", type=int, default=25)
    p_v.add_argument("--format", default="text")
    p_v.add_argument("--no-text", action="store_true")

    p_m = sub.add_parser("compare", help="Compare strategies on one document")
    add_doc_opts(p_m)
    p_m.add_argument("--size", type=int, default=400)

    args = parser.parse_args(argv)
    if args.cmd == "chunk":
        return cmd_chunk(args)
    if args.cmd == "visualize":
        return cmd_visualize(args)
    if args.cmd == "compare":
        return cmd_compare(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
