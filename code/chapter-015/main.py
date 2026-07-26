#!/usr/bin/env python3
"""Chapter 15 CLI — embeddings and semantic search."""

from __future__ import annotations

import argparse
import json

from embedkit.metrics import cosine_similarity
from embedkit.models import BagOfWordsEmbedder, HashingEmbedder, TfidfEmbedder
from embedkit.pipeline import EmbeddingPipeline
from embedkit.search import SemanticSearch, build_default_search


def _model_from_name(name: str, dimensions: int = 128):
    if name == "bow":
        return BagOfWordsEmbedder(dimensions=dimensions)
    if name == "hashing":
        return HashingEmbedder(dimensions=dimensions)
    return TfidfEmbedder()


def cmd_index(model_name: str) -> int:
    svc = SemanticSearch.with_model(_model_from_name(model_name))
    n = svc.index_documents()
    print(
        json.dumps(
            {
                "indexed": n,
                "model_id": svc.pipeline.model_id,
                "dimensions": svc.pipeline.dimensions,
                "ids": svc.index.ids(),
            },
            indent=2,
        )
    )
    return 0


def cmd_search(query: str, k: int, model_name: str, min_score: float | None) -> int:
    svc = SemanticSearch.with_model(_model_from_name(model_name))
    svc.index_documents()
    result = svc.search(query, k=k, min_score=min_score)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_similar(a: str, b: str, model_name: str) -> int:
    svc = SemanticSearch.with_model(_model_from_name(model_name))
    # TF-IDF needs a fit corpus before pairwise compare.
    if isinstance(svc.pipeline.model, TfidfEmbedder) and not svc.pipeline.model.is_fitted:
        svc.index_documents()
    score = svc.similarity(a, b)
    print(
        json.dumps(
            {
                "a": a,
                "b": b,
                "cosine_similarity": score,
                "model_id": svc.pipeline.model_id,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_embed(text: str, model_name: str) -> int:
    model = _model_from_name(model_name)
    if isinstance(model, TfidfEmbedder):
        from embedkit.corpus import load_support_corpus

        model.fit([d.text for d in load_support_corpus()] + [text])
    pipe = EmbeddingPipeline(model)
    vec = pipe.embed_query(text)
    print(
        json.dumps(
            {
                "text": text,
                "model_id": pipe.model_id,
                "dimensions": pipe.dimensions,
                "vector_preview": vec[:8],
                "l2_hint": "vectors are L2-normalized",
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_demo() -> int:
    """Show paraphrase ranking vs unrelated query on the support corpus."""
    svc = build_default_search()
    related = svc.search("How do I get my money back?", k=3)
    unrelated = svc.search("What are the API rate limits?", k=3)
    pair = cosine_similarity(
        svc.pipeline.embed_query("refund policy"),
        svc.pipeline.embed_query("return my payment"),
    )
    print(
        json.dumps(
            {
                "related_query": related.to_dict(),
                "api_query": unrelated.to_dict(),
                "refund_vs_payment_cosine": pair,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 15 — embeddings / semantic search")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_idx = sub.add_parser("index", help="Embed and index the sample support corpus")
    p_idx.add_argument("--model", choices=["tfidf", "hashing", "bow"], default="tfidf")

    p_s = sub.add_parser("search", help="Semantic search over the support corpus")
    p_s.add_argument("query", help="Natural language query")
    p_s.add_argument("-k", type=int, default=3)
    p_s.add_argument("--min-score", type=float, default=None)
    p_s.add_argument("--model", choices=["tfidf", "hashing", "bow"], default="tfidf")

    p_sim = sub.add_parser("similar", help="Cosine similarity between two strings")
    p_sim.add_argument("--a", required=True)
    p_sim.add_argument("--b", required=True)
    p_sim.add_argument("--model", choices=["tfidf", "hashing", "bow"], default="tfidf")

    p_e = sub.add_parser("embed", help="Embed a single string and show a preview")
    p_e.add_argument("text")
    p_e.add_argument("--model", choices=["tfidf", "hashing", "bow"], default="tfidf")

    sub.add_parser("demo", help="Run a small ranking demo on the FAQ corpus")

    args = parser.parse_args(argv)
    if args.cmd == "index":
        return cmd_index(args.model)
    if args.cmd == "search":
        return cmd_search(args.query, args.k, args.model, args.min_score)
    if args.cmd == "similar":
        return cmd_similar(args.a, args.b, args.model)
    if args.cmd == "embed":
        return cmd_embed(args.text, args.model)
    if args.cmd == "demo":
        return cmd_demo()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
