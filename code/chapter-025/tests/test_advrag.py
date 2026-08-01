"""Tests for advanced RAG components."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from advrag.bm25 import BM25Index
from advrag.compress import compress_hit
from advrag.corpus import all_children, build_parent_child_index
from advrag.dense import DenseIndex
from advrag.enterprise import EnterpriseSearch, EnterpriseSearchConfig
from advrag.fusion import reciprocal_rank_fusion
from advrag.hybrid import HybridRetriever
from advrag.parent_child import split_parent_children
from advrag.query_ops import expand_query, multi_queries
from advrag.rerank import SimpleReranker
from advrag.types import Document, SearchHit


def test_bm25_refund():
    idx = BM25Index()
    idx.index(all_children())
    hits = idx.search("refund money back", k=5)
    assert hits
    assert any("billing" in (h.parent_id or h.id) or h.metadata.get("topic") == "billing" for h in hits)


def test_dense_search_runs():
    idx = DenseIndex()
    idx.index(all_children())
    hits = idx.search("password reset two-factor", k=3)
    assert hits


def test_rrf_prefers_consensus():
    a = [
        SearchHit(id="x", text="x", score=10, sources=("bm25",), rank=1),
        SearchHit(id="y", text="y", score=9, sources=("bm25",), rank=2),
    ]
    b = [
        SearchHit(id="x", text="x", score=0.9, sources=("dense",), rank=1),
        SearchHit(id="z", text="z", score=0.8, sources=("dense",), rank=2),
    ]
    fused = reciprocal_rank_fusion([a, b], k=3)
    assert fused[0].id == "x"
    assert set(fused[0].sources) >= {"bm25", "dense"}


def test_hybrid_mode():
    ret = HybridRetriever()
    ret.index(all_children())
    h = ret.search("HTTP 429 rate limit", k=3, mode="hybrid")
    assert h
    b = ret.search("HTTP 429 rate limit", k=3, mode="bm25")
    d = ret.search("HTTP 429 rate limit", k=3, mode="dense")
    assert b and d


def test_expand_and_multi():
    exp = expand_query("How do I get a refund?")
    assert len(exp) >= 2
    mq = multi_queries("refund please", n=3)
    assert len(mq) == 3


def test_parent_child_expand():
    pci = build_parent_child_index()
    kids = pci.all_indexable()
    assert all(k.parent_id for k in kids)
    # fake child hit
    child = kids[0]
    hit = SearchHit(
        id=child.id,
        text=child.text,
        score=1.0,
        metadata=child.metadata,
        parent_id=child.parent_id,
        sources=("dense",),
        rank=1,
    )
    parents = pci.expand_to_parents([hit], k=1)
    assert parents[0].id == child.parent_id
    assert "parent_expand" in parents[0].sources


def test_split_parent_children():
    parent = Document(id="p", text="a" * 500, metadata={"t": 1})
    kids = split_parent_children(parent, child_size=100, overlap=20)
    assert len(kids) >= 4
    assert all(k.parent_id == "p" for k in kids)


def test_compress_shortens():
    hit = SearchHit(
        id="h",
        text="Alpha refund money back within thirty days. Unrelated warehouse trivia follows here. More noise about offices.",
        score=1.0,
        metadata={},
        sources=("bm25",),
        rank=1,
    )
    c = compress_hit("refund money", hit, max_chars=80)
    assert len(c.text) <= 120
    assert "compressed" in c.metadata


def test_rerank_changes_order_with_overlap():
    hits = [
        SearchHit(id="weak", text="general platform notes", score=0.99, metadata={"title": "Notes"}, sources=("dense",), rank=1),
        SearchHit(id="strong", text="refund money back reverse charge", score=0.2, metadata={"title": "Refund"}, sources=("bm25",), rank=2),
    ]
    out = SimpleReranker(alpha=0.2, beta=0.7, gamma=0.1).rerank("refund money back", hits, k=2)
    assert out[0].id == "strong"


def test_enterprise_search_refund():
    eng = EnterpriseSearch.with_default_corpus()
    r = eng.search("How do I get my money back?")
    assert r.hits
    assert r.expanded_queries
    # billing parent should appear
    assert any("billing" in h.id or h.metadata.get("topic") == "billing" for h in r.hits)


def test_enterprise_filter_topic():
    eng = EnterpriseSearch.with_default_corpus()
    r = eng.search("security password SSO", filters={"topic": "security"})
    assert r.hits
    assert all(h.metadata.get("topic") == "security" for h in r.hits)


def test_config_toggles():
    eng = EnterpriseSearch.with_default_corpus(
        config=EnterpriseSearchConfig(
            multi_query=False,
            use_expansion=False,
            parent_expand=False,
            compress=False,
            rerank=False,
            final_k=2,
        )
    )
    r = eng.search("API rate limits")
    assert len(r.hits) <= 2
    assert r.diagnostics["parent_expand"] is False
    assert r.diagnostics["compress"] is False
    assert r.diagnostics["rerank"] is False
    assert r.diagnostics["n_query_variants"] == 1
