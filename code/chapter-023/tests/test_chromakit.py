"""Tests for Chroma store and knowledge assistant."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chromakit.assistant import KnowledgeAssistant
from chromakit.corpus import knowledge_docs
from chromakit.embeddings import HashEmbeddingFunction
from chromakit.store import ChromaStore


def test_hash_embedding_dim():
    ef = HashEmbeddingFunction(32)
    vecs = ef(["hello world", "refund money"])
    assert len(vecs) == 2
    assert len(vecs[0]) == 32
    n = sum(x * x for x in vecs[0]) ** 0.5
    assert abs(n - 1.0) < 1e-5


def test_upsert_and_query_ephemeral():
    store = ChromaStore("knowledge_base", path=None, dimensions=64)
    store.upsert_docs(knowledge_docs())
    assert store.count() == len(knowledge_docs())
    r = store.query("How do I get my money back?", n_results=3)
    assert r.hits
    assert r.hits[0].id == "kb-refund"
    assert r.backend == "ephemeral"


def test_metadata_filter():
    store = ChromaStore("knowledge_base", dimensions=64)
    store.upsert_docs(knowledge_docs())
    r = store.query("security login SSO", n_results=5, where={"topic": "security"})
    assert r.hits
    assert all(h.metadata.get("topic") == "security" for h in r.hits)


def test_persistent_roundtrip(tmp_path: Path):
    path = tmp_path / "chroma_data"
    s1 = ChromaStore("knowledge_base", path=path, dimensions=64)
    s1.upsert_docs(knowledge_docs()[:3])
    assert s1.count() == 3
    s2 = ChromaStore("knowledge_base", path=path, dimensions=64)
    assert s2.count() == 3
    r = s2.query("shipping tracking", n_results=1)
    assert r.hits


def test_delete():
    store = ChromaStore("knowledge_base", dimensions=64)
    store.upsert_docs(knowledge_docs())
    store.delete(["kb-sla"])
    ids = {h.id for h in store.query("uptime SLA credits", n_results=5).hits}
    assert "kb-sla" not in ids or store.count() == len(knowledge_docs()) - 1


def test_assistant_grounded_answer():
    asst = KnowledgeAssistant(path=None, dimensions=64)
    asst.ingest_default()
    ans = asst.ask("How do I get my money back?", n_results=2)
    assert ans.grounded
    assert ans.citations
    assert "kb-refund" in [c["id"] for c in ans.citations]
    assert "refund" in ans.answer.lower() or "money" in ans.answer.lower()


def test_assistant_filter_topic():
    asst = KnowledgeAssistant(dimensions=64)
    asst.ingest_default()
    ans = asst.ask("authentication", n_results=3, where={"topic": "security"})
    assert ans.citations
    assert all(c.get("topic") == "security" for c in ans.citations)


def test_stats_and_list():
    store = ChromaStore("knowledge_base", dimensions=64)
    store.upsert_docs(knowledge_docs()[:1])
    st = store.stats()
    assert st["count"] >= 1
    assert "knowledge_base" in store.list_collections()


def test_collection_name_validation():
    with pytest.raises(ValueError):
        ChromaStore("ab", dimensions=32)
