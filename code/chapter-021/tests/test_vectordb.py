"""Tests for mini vector database."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vectordb.compare import compare_indexes
from vectordb.database import VectorDB
from vectordb.demo_data import DOCS, QUERIES
from vectordb.filter import matches
from vectordb.persist import load_db, save_db


def _seed(col, docs=DOCS):
    col.upsert_many(docs)


def test_flat_search_refund():
    db = VectorDB()
    col = db.create_collection("kb", index_type="flat")
    _seed(col)
    r = col.query(text="How do I get my money back?", k=3)
    assert r.hits
    assert r.hits[0].id == "refund"
    assert r.n_scanned == len(DOCS)


def test_metadata_filter_tenant():
    db = VectorDB()
    col = db.create_collection("kb", index_type="flat")
    _seed(col)
    r = col.query(text="security login SSO", k=5, where={"tenant": "globex"})
    assert r.hits
    assert all(h.metadata.get("tenant") == "globex" for h in r.hits)


def test_filter_operators():
    meta = {"topic": "billing", "priority": 2}
    assert matches(meta, {"topic": "billing"})
    assert matches(meta, {"priority": {"$gte": 2}})
    assert matches(meta, {"topic": {"$in": ["billing", "legal"]}})
    assert not matches(meta, {"priority": {"$lt": 2}})
    assert matches(meta, {"$and": [{"topic": "billing"}, {"priority": {"$lte": 2}}]})


def test_ivf_builds_and_searches():
    db = VectorDB()
    col = db.create_collection("kb", index_type="ivf", nlist=4, nprobe=2)
    _seed(col)
    col.rebuild()
    r = col.query(text="rate limit 429", k=3)
    assert r.hits
    assert r.n_scanned <= len(DOCS)
    assert r.index_type == "ivf"


def test_delete_and_get():
    db = VectorDB()
    col = db.create_collection("kb", index_type="flat")
    _seed(col)
    assert col.get("sla") is not None
    assert col.delete("sla")
    assert col.get("sla") is None
    ids = {h.id for h in col.query(text="uptime SLA", k=5).hits}
    assert "sla" not in ids


def test_persist_roundtrip(tmp_path: Path):
    db = VectorDB()
    col = db.create_collection("kb", index_type="flat")
    _seed(col)
    path = tmp_path / "db.json"
    save_db(db, path)
    db2 = load_db(path)
    r = db2.get_collection("kb").query(text="password reset", k=1)
    assert r.hits[0].id == "auth"


def test_dim_mismatch():
    db = VectorDB()
    col = db.create_collection("kb", index_type="flat", dimensions=8)
    col.upsert(id="a", vector=[1.0] + [0.0] * 7, text="a")
    with pytest.raises(ValueError):
        col.upsert(id="b", vector=[1.0, 0.0], text="b")


def test_compare_indexes():
    rep = compare_indexes(DOCS, QUERIES[:3], k=2, nlist=4, nprobe=2)
    assert rep["n_docs"] == len(DOCS)
    assert rep["avg_flat_scanned"] >= rep["avg_ivf_scanned"]
    assert 0.0 <= rep["top1_agreement"] <= 1.0


def test_collection_stats():
    db = VectorDB()
    col = db.create_collection("kb", index_type="flat")
    _seed(col)
    st = col.stats()
    assert st.count == len(DOCS)
    assert "topic" in st.metadata_keys


def test_list_delete_collection():
    db = VectorDB()
    db.create_collection("a")
    db.create_collection("b")
    assert db.list_collections() == ["a", "b"]
    assert db.delete_collection("a")
    assert db.list_collections() == ["b"]


def test_min_score():
    db = VectorDB()
    col = db.create_collection("kb", index_type="flat")
    _seed(col)
    r = col.query(text="refund", k=10, min_score=0.99)
    assert all(h.score >= 0.99 for h in r.hits)
