"""Tests for embedding pipeline and semantic search."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from embedkit.corpus import load_support_corpus
from embedkit.index import DimensionMismatchError, InMemoryVectorIndex, ModelMismatchError
from embedkit.metrics import cosine_similarity, euclidean_distance, l2_normalize, l2_norm
from embedkit.models import BagOfWordsEmbedder, HashingEmbedder, TfidfEmbedder
from embedkit.normalize import normalize_text
from embedkit.pipeline import EmbeddingPipeline
from embedkit.search import SemanticSearch, build_default_search
from embedkit.types import Document, VectorRecord


def test_normalize_unicode_and_case():
    assert normalize_text("  Hello   WORLD  ") == "hello world"
    # full-width digits folded by NFKC
    assert "1" in normalize_text("１")


def test_l2_normalize_unit_length():
    v = l2_normalize([3.0, 4.0])
    assert abs(l2_norm(v) - 1.0) < 1e-9
    assert abs(v[0] - 0.6) < 1e-9


def test_cosine_and_euclidean():
    a = [1.0, 0.0]
    b = [1.0, 0.0]
    c = [0.0, 1.0]
    assert abs(cosine_similarity(a, b) - 1.0) < 1e-9
    assert abs(cosine_similarity(a, c)) < 1e-9
    assert euclidean_distance(a, b) == 0.0
    assert abs(euclidean_distance(a, c) - (2**0.5)) < 1e-9


def test_dimension_mismatch_metrics():
    with pytest.raises(ValueError, match="dimension"):
        cosine_similarity([1.0], [1.0, 2.0])


def test_hashing_embedder_stable_and_unit():
    m = HashingEmbedder(dimensions=64)
    v1 = m.embed(["Refund policy money back"])[0]
    v2 = m.embed(["Refund policy money back"])[0]
    assert v1 == v2
    assert abs(l2_norm(v1) - 1.0) < 1e-6
    assert len(v1) == 64
    assert m.model_id


def test_pipeline_embed_documents():
    pipe = EmbeddingPipeline(HashingEmbedder(dimensions=32))
    docs = [Document(id="a", text="hello"), Document(id="b", text="world")]
    recs = pipe.embed_documents(docs)
    assert len(recs) == 2
    assert recs[0].model_id == pipe.model_id
    assert recs[0].dim == 32


def test_index_upsert_and_search():
    model = TfidfEmbedder()
    docs = load_support_corpus()
    model.fit([d.text for d in docs])
    pipe = EmbeddingPipeline(model)
    recs = pipe.embed_documents(docs)
    idx = InMemoryVectorIndex()
    idx.upsert_many(recs)
    q = pipe.embed_query("How do I reverse a charge and get money back?")
    hits = idx.search(q, k=3, model_id=pipe.model_id)
    assert len(hits) == 3
    assert hits[0].score >= hits[-1].score
    assert hits[0].id == "faq-refund"


def test_index_rejects_dim_and_model_mix():
    idx = InMemoryVectorIndex()
    r1 = VectorRecord(
        id="x",
        vector=tuple(l2_normalize([1.0, 0.0, 0.0, 0.0])),
        text="t",
        metadata={},
        model_id="m1",
        dim=4,
    )
    idx.upsert(r1)
    with pytest.raises(DimensionMismatchError):
        idx.search([1.0, 0.0], k=1)
    with pytest.raises(ModelMismatchError):
        idx.search([1.0, 0.0, 0.0, 0.0], k=1, model_id="other")
    bad = VectorRecord(
        id="y",
        vector=tuple(l2_normalize([0.0, 1.0, 0.0, 0.0])),
        text="t",
        metadata={},
        model_id="m2",
        dim=4,
    )
    with pytest.raises(ModelMismatchError):
        idx.upsert(bad)


def test_semantic_search_paraphrase_ranks_refund():
    svc = build_default_search()
    result = svc.search("How do I get my money back?", k=3)
    assert result.index_size == len(load_support_corpus())
    ids = [h.id for h in result.hits]
    assert "faq-refund" in ids
    # Content-token hashing should put refund first for money-back paraphrases.
    assert ids[0] == "faq-refund"


def test_related_pair_outranks_unrelated_similarity():
    svc = build_default_search()
    # Pairwise cosine needs shared content tokens (TF-IDF is lexical).
    related = svc.similarity("refund money back charge", "money back reverse charge")
    unrelated = svc.similarity("refund money back charge", "api rate limit 429 backoff")
    assert related > unrelated
    assert related > 0.0


def test_bow_embedder_search_runs():
    svc = SemanticSearch.with_model(BagOfWordsEmbedder(dimensions=96))
    svc.index_documents()
    hits = svc.search("password reset two-factor", k=2).hits
    assert hits
    assert any("auth" in h.id or "password" in h.text.lower() for h in hits)


def test_min_score_filters():
    svc = build_default_search()
    # absurdly high threshold → empty
    empty = svc.search("refund", k=5, min_score=0.9999)
    assert empty.hits == [] or all(h.score >= 0.9999 for h in empty.hits)


def test_tfidf_fit_required():
    m = TfidfEmbedder()
    with pytest.raises(RuntimeError, match="fit"):
        m.embed(["hello"])
    m.fit(["refund money back", "api rate limits"])
    vecs = m.embed(["money back"])
    assert len(vecs[0]) == m.dimensions
    assert abs(sum(x * x for x in vecs[0]) - 1.0) < 1e-6
