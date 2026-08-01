"""Tests for FAISS service and PDF search."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from faisskit.embed import HashEmbedder
from faisskit.optimize import compare_kinds, sweep_nprobe
from faisskit.pdf_io import extract_text, write_text_pdf
from faisskit.pdf_search import PdfSearchEngine, build_sample_pdfs, chunk_pages
from faisskit.persist import load_service, save_service
from faisskit.service import FaissIndexService


DOCS = [
    {"id": "refund", "text": "Refund money back reverse charge 30 days unused", "metadata": {"topic": "billing"}},
    {"id": "ship", "text": "Shipping tracking express delivery business days", "metadata": {"topic": "logistics"}},
    {"id": "auth", "text": "Password reset two-factor authentication security", "metadata": {"topic": "security"}},
    {"id": "api", "text": "API rate limits HTTP 429 backoff retry", "metadata": {"topic": "developers"}},
]


def test_embed_normalized():
    e = HashEmbedder(32)
    v = e.embed(["hello world"])
    assert v.shape == (1, 32)
    assert abs(float(np.linalg.norm(v[0])) - 1.0) < 1e-5


def test_flat_search():
    svc = FaissIndexService(kind="flat_ip", dimensions=64)
    svc.add_documents(DOCS)
    r = svc.search("money back refund", k=2)
    assert r.hits
    assert r.hits[0].id == "refund"
    assert r.ntotal == len(DOCS)


def test_ivf_and_hnsw_build():
    for kind in ("ivf_flat", "hnsw"):
        svc = FaissIndexService(kind=kind, dimensions=64, nlist=2, nprobe=1)
        svc.add_documents(DOCS)
        r = svc.search("password reset", k=2)
        assert r.hits
        assert svc.ntotal == len(DOCS)


def test_metadata_filter():
    svc = FaissIndexService(kind="flat_ip", dimensions=64)
    svc.add_documents(DOCS)
    r = svc.search("security authentication", k=5, where={"topic": "security"})
    assert r.hits
    assert all(h.metadata.get("topic") == "security" for h in r.hits)


def test_remove():
    svc = FaissIndexService(kind="flat_ip", dimensions=64)
    svc.add_documents(DOCS)
    assert svc.remove("api")
    ids = {h.id for h in svc.search("HTTP 429", k=5).hits}
    assert "api" not in ids


def test_persist_roundtrip(tmp_path: Path):
    svc = FaissIndexService(kind="hnsw", dimensions=64)
    svc.add_documents(DOCS)
    save_service(svc, tmp_path / "idx")
    svc2 = load_service(tmp_path / "idx")
    assert svc2.ntotal == len(DOCS)
    assert svc2.search("refund money", k=1).hits[0].id == "refund"


def test_compare_kinds():
    rep = compare_kinds(DOCS, ["refund money", "shipping tracking"], dimensions=64, k=2)
    kinds = {r["kind"] for r in rep["results"]}
    assert "flat_ip" in kinds
    assert all(0.0 <= r["top1_agreement_vs_flat"] <= 1.0 for r in rep["results"])


def test_nprobe_sweep():
    docs = []
    for i, d in enumerate(DOCS * 2):
        docs.append({**d, "id": f"{d['id']}_{i}"})
    svc = FaissIndexService(kind="ivf_flat", dimensions=64, nlist=2, nprobe=1)
    svc.add_documents(docs)
    rows = sweep_nprobe(svc, ["refund"], nprobes=[1, 2])
    assert len(rows) == 2
    assert "nprobe" in rows[0]


def test_pdf_write_extract_search(tmp_path: Path):
    pdf = write_text_pdf(
        tmp_path / "t.pdf",
        ["Refund policy money back within thirty days.", "Shipping tracking numbers emailed."],
        title="T",
    )
    pages = extract_text(pdf)
    assert any("Refund" in p or "money" in p for p in pages)
    engine = PdfSearchEngine.from_pdfs([pdf], kind="flat_ip", dimensions=64)
    r = engine.search("money back refund", k=2)
    assert r.hits
    assert r.hits[0].metadata.get("page") is not None


def test_build_sample_pdfs_and_search(tmp_path: Path):
    paths = build_sample_pdfs(tmp_path)
    assert len(paths) == 3
    engine = PdfSearchEngine.from_pdfs(paths, kind="flat_ip")
    r = engine.search("How do I get a refund?", k=3)
    assert r.hits
    # top hit should come from refund policy pdf
    assert "refund" in r.hits[0].metadata.get("source", "").lower() or "refund" in r.hits[0].text.lower()


def test_chunk_pages():
    docs = chunk_pages(["a" * 900], source="x.pdf", max_chars=300)
    assert len(docs) >= 3
    assert docs[0]["metadata"]["source"] == "x.pdf"
