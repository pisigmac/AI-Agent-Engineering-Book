"""Run retrieval benchmarks across embedders."""

from __future__ import annotations

import time
from typing import Sequence

from embbench.catalog import catalog_by_id
from embbench.dataset import all_pairs, corpus_texts, english_pairs, multilingual_pairs
from embbench.metrics import mrr, rank_documents, recall_at_k
from embbench.models import (
    CharNgramEmbedder,
    HashingEmbedder,
    TfidfEmbedder,
    build_teaching_embedder,
)
from embbench.types import CompareReport, Embedder, LabeledPair, ModelBenchResult


def _estimate_query_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _storage_bytes(dim: int, n_docs: int = 1000, bytes_per_float: int = 4) -> int:
    return dim * n_docs * bytes_per_float


def prepare_embedder(model_id: str, fit_texts: Sequence[str]) -> Embedder:
    if model_id.startswith("teaching:"):
        emb = build_teaching_embedder(model_id)
        if isinstance(emb, TfidfEmbedder):
            emb.fit(list(fit_texts))
        return emb
    # Simulated commercial/local models: map to teaching proxies with different dims
    # so the harness is offline but catalog-driven.
    card = catalog_by_id()[model_id]
    if card.multilingual and (
        "e5" in model_id or "multilingual" in model_id or "cohere" in model_id or "voyage" in model_id
    ):
        dim = card.dimensions if card.dimensions > 0 else 256
        return CharNgramEmbedder(dimensions=min(dim, 512), model_id=model_id)
    if card.family.value == "open_weights" or "minilm" in model_id:
        return HashingEmbedder(dimensions=min(card.dimensions, 384) if card.dimensions else 256, model_id=model_id)
    # API general: char n-gram mid quality proxy
    return CharNgramEmbedder(
        dimensions=min(card.dimensions, 512) if card.dimensions else 256,
        model_id=model_id,
    )


def benchmark_embedder(
    embedder: Embedder,
    pairs: list[LabeledPair],
    corpus: dict[str, str],
    *,
    cost_per_1m: float = 0.0,
) -> ModelBenchResult:
    doc_ids = list(corpus.keys())
    doc_texts = [corpus[i] for i in doc_ids]

    t0 = time.perf_counter()
    # Fit path already done for tfidf
    doc_vecs = embedder.embed(doc_texts)
    r1_scores: list[float] = []
    r3_scores: list[float] = []
    rr_scores: list[float] = []
    multi_r1: list[float] = []
    total_q_tokens = 0

    for pair in pairs:
        qv = embedder.embed([pair.query])[0]
        ranked = rank_documents(qv, doc_ids, doc_vecs)
        ranked_ids = [d for d, _ in ranked]
        rel = {pair.positive}
        r1_scores.append(recall_at_k(ranked_ids, rel, 1))
        r3_scores.append(recall_at_k(ranked_ids, rel, 3))
        rr_scores.append(mrr(ranked_ids, rel))
        if pair.lang != "en":
            multi_r1.append(recall_at_k(ranked_ids, rel, 1))
        total_q_tokens += _estimate_query_tokens(pair.query)

    elapsed_ms = (time.perf_counter() - t0) * 1000
    n = max(len(pairs), 1)
    avg_lat = elapsed_ms / n
    # cost for 1000 queries of average token length from this run
    avg_q_tok = total_q_tokens / n
    cost_1k = (1000 * avg_q_tok / 1_000_000.0) * cost_per_1m
    # plus rough doc embedding amortized ignored for query-side compare

    dim = getattr(embedder, "dimensions", 0) or (len(doc_vecs[0]) if doc_vecs else 0)
    notes: list[str] = []
    if isinstance(embedder, TfidfEmbedder):
        notes.append("lexical TF-IDF; English keyword-heavy")
    if isinstance(embedder, CharNgramEmbedder):
        notes.append("char n-grams help multilingual surface forms offline")
    if cost_per_1m == 0.0:
        notes.append("zero API cost (local/teaching) — infra still costs")

    return ModelBenchResult(
        model_id=embedder.model_id,
        dimensions=int(dim),
        recall_at_1=sum(r1_scores) / n,
        recall_at_3=sum(r3_scores) / n,
        mrr=sum(rr_scores) / n,
        multilingual_recall_at_1=(sum(multi_r1) / len(multi_r1)) if multi_r1 else 0.0,
        avg_latency_ms=avg_lat,
        est_cost_per_1k_queries_usd=cost_1k,
        storage_bytes_per_1k_docs=_storage_bytes(int(dim) or 1),
        n_pairs=len(pairs),
        notes=notes,
    )


def run_benchmark(
    model_ids: list[str] | None = None,
    *,
    include_multilingual: bool = True,
) -> CompareReport:
    catalog = catalog_by_id()
    if model_ids is None:
        model_ids = [
            "teaching:tfidf",
            "teaching:hashing",
            "teaching:char-ngram",
            "local:minilm-l6",
            "local:e5-multilingual-small",
            "openai:text-embedding-3-small",
            "cohere:embed-multilingual-v3",
        ]
    corpus = corpus_texts()
    pairs = all_pairs() if include_multilingual else english_pairs()
    fit_texts = list(corpus.values()) + [p.query for p in pairs]

    results: list[ModelBenchResult] = []
    for mid in model_ids:
        if mid not in catalog and not mid.startswith("teaching:"):
            raise KeyError(f"unknown model_id: {mid}")
        emb = prepare_embedder(mid, fit_texts)
        # ensure model_id on proxy matches requested
        if not mid.startswith("teaching:"):
            emb.model_id = mid  # type: ignore[attr-defined]
        cost = catalog[mid].cost_per_1m_tokens if mid in catalog else 0.0
        results.append(benchmark_embedder(emb, pairs, corpus, cost_per_1m=cost))

    by_mrr = sorted(results, key=lambda r: (-r.mrr, r.est_cost_per_1k_queries_usd, r.model_id))
    # cost efficiency: mrr / (cost + epsilon) — prefer quality per dollar
    def eff(r: ModelBenchResult) -> float:
        return r.mrr / (r.est_cost_per_1k_queries_usd + 1e-9)

    by_eff = sorted(results, key=lambda r: (-eff(r), -r.mrr, r.model_id))

    best = by_mrr[0]
    multi_sorted = sorted(results, key=lambda r: (-r.multilingual_recall_at_1, -r.mrr))
    rationale = [
        f"Best MRR on this harness: {best.model_id} (MRR={best.mrr:.3f}).",
        f"Best multilingual R@1: {multi_sorted[0].model_id} "
        f"({multi_sorted[0].multilingual_recall_at_1:.3f}).",
        "Teaching models are offline proxies — validate neural/API models on your corpus.",
    ]
    # Recommendation heuristic
    multi_need = any(p.lang != "en" for p in pairs)
    if multi_need and multi_sorted[0].multilingual_recall_at_1 >= best.mrr - 0.05:
        rec = multi_sorted[0].model_id
        rationale.append("Prefer multilingual-capable model when non-EN queries matter.")
    else:
        # prefer free if quality close
        free = [r for r in by_mrr if r.est_cost_per_1k_queries_usd == 0.0]
        if free and free[0].mrr >= best.mrr - 0.1:
            rec = free[0].model_id
            rationale.append("Local/teaching quality close to best — good default for privacy/cost.")
        else:
            rec = best.model_id
            rationale.append("Quality gap favors the top MRR model for this dataset.")

    return CompareReport(
        results=results,
        ranking_by_mrr=[r.model_id for r in by_mrr],
        ranking_by_cost_efficiency=[r.model_id for r in by_eff],
        recommendation=rec,
        rationale=rationale,
    )


def tradeoff_matrix() -> list[dict]:
    """Static qualitative trade-off table from catalog."""
    rows = []
    for c in catalog_by_id().values():
        rows.append(
            {
                "model_id": c.model_id,
                "dims": c.dimensions,
                "cost_per_1m": c.cost_per_1m_tokens,
                "multilingual": c.multilingual,
                "family": c.family.value,
                "latency": c.latency_class,
                "max_tokens": c.max_tokens,
                "notes": c.notes,
            }
        )
    return rows
