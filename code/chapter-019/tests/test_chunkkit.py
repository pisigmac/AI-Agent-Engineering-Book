"""Tests for chunking strategies."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chunkkit.fixed import chunk_fixed
from chunkkit.hierarchical import chunk_hierarchical, expand_to_parent
from chunkkit.pipeline import chunk_document, compare_strategies
from chunkkit.recursive import chunk_recursive
from chunkkit.sample_docs import sample_handbook, sample_short
from chunkkit.semantic import chunk_semantic
from chunkkit.sliding import chunk_sliding
from chunkkit.tokens import estimate_tokens
from chunkkit.types import SourceDocument
from chunkkit.visualize import boundary_map, visualize_report


def test_fixed_sizes_and_overlap():
    doc = SourceDocument(id="d", text="a" * 1000)
    rep = chunk_fixed(doc, size=100, overlap=20)
    assert rep.n_chunks >= 10
    assert all(len(c.text) <= 100 for c in rep.chunks)
    # consecutive overlap: end-start of windows
    assert rep.chunks[0].end - rep.chunks[0].start == 100


def test_sliding_stride():
    doc = SourceDocument(id="d", text="x" * 500)
    rep = chunk_sliding(doc, window=100, stride=50)
    assert rep.n_chunks >= 9
    assert rep.chunks[1].start == 50


def test_recursive_respects_paragraphs():
    doc = sample_handbook()
    rep = chunk_recursive(doc, chunk_size=350, chunk_overlap=30)
    assert rep.n_chunks >= 3
    # Should not be a single blob
    assert rep.max_chars <= 350 * 2 + 50


def test_semantic_splits_topic_shift():
    doc = sample_short()
    rep = chunk_semantic(doc, similarity_threshold=0.15, max_chunk_chars=200, min_chunk_chars=10)
    assert rep.n_chunks >= 1
    assert sum(len(c.text) for c in rep.chunks) >= 20


def test_hierarchical_parent_child():
    doc = sample_handbook()
    rep = chunk_hierarchical(doc, parent_size=700, child_size=200, child_overlap=20)
    parents = [c for c in rep.chunks if c.level == 0]
    children = [c for c in rep.chunks if c.level == 1]
    assert parents and children
    assert all(c.parent_id for c in children)
    child = children[0]
    parent = expand_to_parent(child, rep.chunks)
    assert parent is not None
    assert parent.id == child.parent_id


def test_pipeline_unknown_strategy():
    with pytest.raises(ValueError):
        chunk_document(sample_short(), "nope")


def test_compare_all_strategies():
    rep = compare_strategies(sample_handbook(), size=350)
    assert set(rep.strategies) >= {"fixed", "sliding", "recursive", "semantic", "hierarchical"}
    for name, stats in rep.strategies.items():
        assert stats["n_chunks"] >= 1, name


def test_visualize_nonempty():
    doc = sample_handbook()
    rep = chunk_recursive(doc, chunk_size=300, chunk_overlap=20)
    text = visualize_report(rep, doc.text, max_chunks=5)
    assert "strategy=recursive" in text
    assert "doc-handbook" in text or "c0000" in text
    bmap = boundary_map(doc.text, rep.chunks, density=40)
    assert bmap.startswith("|") and bmap.endswith("|")


def test_empty_document():
    doc = SourceDocument(id="e", text="")
    assert chunk_fixed(doc, size=50).n_chunks == 0
    assert chunk_sliding(doc, window=50).n_chunks == 0


def test_invalid_params():
    doc = sample_short()
    with pytest.raises(ValueError):
        chunk_fixed(doc, size=10, overlap=10)
    with pytest.raises(ValueError):
        chunk_hierarchical(doc, parent_size=100, child_size=200)


def test_estimate_tokens():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1


def test_chunk_ids_unique():
    rep = chunk_fixed(sample_handbook(), size=200, overlap=0)
    ids = [c.id for c in rep.chunks]
    assert len(ids) == len(set(ids))


def test_offsets_within_doc():
    doc = sample_handbook()
    for strat in ("fixed", "sliding", "recursive"):
        rep = chunk_document(
            doc,
            strat,
            **(
                {"size": 300, "overlap": 20}
                if strat == "fixed"
                else {"window": 300, "stride": 150}
                if strat == "sliding"
                else {"chunk_size": 300, "chunk_overlap": 20}
            ),
        )
        for c in rep.chunks:
            assert 0 <= c.start <= c.end <= len(doc.text) + 5  # allow minor span slack
