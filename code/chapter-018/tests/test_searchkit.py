"""Tests for semantic search engine."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from searchkit.corpus import knowledge_base, labeled_queries
from searchkit.embed import HashingEmbedder, TfidfEmbedder
from searchkit.engine import SearchEngine
from searchkit.eval import evaluate, precision_at_k, recall_at_k, reciprocal_rank
from searchkit.persist import load_engine, save_engine
from searchkit.rank import apply_metadata_boosts, mmr_rerank
from searchkit.types import Document, SearchHit, VectorRecord


def test_ingest_and_stats():
    eng = SearchEngine.with_defaults()
    st = eng.stats()
    assert st["documents"] == len(knowledge_base())
    assert st["vectors"] == st["documents"]
    assert st["dimensions"] > 0


def test_refund_paraphrase_ranks_first():
    eng = SearchEngine.with_defaults()
    r = eng.search("How do I get my money back?", k=3)
    assert r.hits
    assert r.hits[0].id == "kb-refund"


def test_metadata_filter_topic():
    eng = SearchEngine.with_defaults()
    r = eng.search("limits", k=10, filters={"topic": "developers"})
    assert r.hits
    assert all(h.metadata.get("topic") == "developers" for h in r.hits)


def test_min_score_filter():
    eng = SearchEngine.with_defaults()
    r = eng.search("refund", k=10, min_score=0.99)
    assert all(h.score >= 0.99 for h in r.hits)


def test_mmr_returns_k():
    eng = SearchEngine.with_defaults()
    r = eng.search("billing payment plan", k=3, strategy="mmr")
    assert len(r.hits) <= 3
    assert r.strategy == "mmr"
    if r.hits:
        assert "mmr" in r.hits[0].score_components


def test_boost_strategy_runs():
    eng = SearchEngine.with_defaults()
    r = eng.search(
        "money",
        k=5,
        strategy="boost",
        boosts={"topic": {"billing": 1.5}},
    )
    assert r.hits
    assert r.hits[0].rank == 1


def test_explain_overlap():
    eng = SearchEngine.with_defaults()
    exp = eng.explain("refund money back", "kb-refund")
    assert exp["ok"]
    assert exp["cosine"] > 0
    assert "refund" in exp["token_overlap"] or "money" in exp["token_overlap"]


def test_eval_metrics_reasonable():
    eng = SearchEngine.with_defaults()
    report = eng.evaluate_default(k=3)
    assert report.n_queries == len(labeled_queries())
    assert report.recall_at_k >= 0.75
    assert report.mrr >= 0.6


def test_persist_roundtrip(tmp_path: Path):
    eng = SearchEngine.with_defaults()
    path = tmp_path / "idx.json"
    save_engine(eng, path)
    eng2 = load_engine(path)
    r1 = eng.search("password reset", k=1)
    r2 = eng2.search("password reset", k=1)
    assert r1.hits[0].id == r2.hits[0].id


def test_delete_document():
    eng = SearchEngine.with_defaults()
    assert eng.delete("kb-sla")
    ids = {h.id for h in eng.search("uptime SLA credit", k=5).hits}
    assert "kb-sla" not in ids


def test_hashing_model_search():
    eng = SearchEngine(model=HashingEmbedder(64))
    eng.ingest(knowledge_base()[:4], rebuild=True)
    r = eng.search("shipping delivery", k=2)
    assert r.hits


def test_recall_precision_rr_unit():
    hits = [
        SearchHit(id="a", score=1.0, text=""),
        SearchHit(id="b", score=0.5, text=""),
    ]
    rel = {"b"}
    assert recall_at_k(hits, rel, 2) == 1.0
    assert precision_at_k(hits, rel, 2) == 0.5
    assert reciprocal_rank(hits, rel) == 0.5


def test_mmr_diversity_prefers_different_docs():
    # two near-duplicate vectors + one diverse
    q = [1.0, 0.0]
    hits = [
        SearchHit(id="d1", score=0.99, text="t1"),
        SearchHit(id="d2", score=0.98, text="t2"),
        SearchHit(id="d3", score=0.5, text="t3"),
    ]
    recs = {
        "d1": VectorRecord("d1", (1.0, 0.0), "t1", {}, "m", 2),
        "d2": VectorRecord("d2", (0.99, 0.01), "t2", {}, "m", 2),
        "d3": VectorRecord("d3", (0.0, 1.0), "t3", {}, "m", 2),
    }
    # normalize-ish already unit-ish
    out = mmr_rerank(hits, recs, q, lambda_mult=0.5, k=2)
    assert out[0].id == "d1"
    # second should favor diversity → d3 often
    assert out[1].id in {"d2", "d3"}


def test_ingest_custom_doc():
    eng = SearchEngine()
    eng.ingest(
        [Document(id="x", text="alpha beta gamma uniquephrase", title="X", metadata={"topic": "test"})],
        rebuild=True,
    )
    r = eng.search("uniquephrase", k=1)
    assert r.hits[0].id == "x"
