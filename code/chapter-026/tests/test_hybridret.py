from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hybridret import HybridRetriever
from hybridret.corpus import LABELS

def test_index_and_modes():
    r = HybridRetriever(); assert r.index() == 10
    for mode in ["bm25", "dense", "sparse", "hybrid_rrf", "hybrid_weighted"]:
        hits = r.search("HTTP 429", k=3, mode=mode)
        assert hits

def test_error_code_bm25_strong():
    r = HybridRetriever(); r.index()
    hits = r.search("E-4032 payment gateway", k=3, mode="bm25")
    assert hits[0].id == "d-error"

def test_hybrid_eval():
    r = HybridRetriever(); r.index()
    rep = r.eval_modes(k=3)
    assert rep["hybrid_rrf"]["recall_at_k"] >= 0.75
    assert rep["bm25"]["n_queries"] == len(LABELS)

def test_compare_keys():
    r = HybridRetriever(); r.index()
    c = r.compare("refund money")
    assert set(c) >= {"bm25", "dense", "hybrid_rrf"}
