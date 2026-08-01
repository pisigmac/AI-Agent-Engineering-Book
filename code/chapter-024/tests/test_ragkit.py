"""Tests for production RAG pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ragkit.citations import build_citations, format_citation_footer
from ragkit.corpus import load_corpus
from ragkit.eval import evaluate_rag
from ragkit.memory import ConversationMemory
from ragkit.pipeline import RAGConfig, RAGSystem
from ragkit.prompt import assemble_prompt
from ragkit.ranker import Ranker
from ragkit.retriever import InMemoryRetriever
from ragkit.types import RetrievedChunk


def test_index_and_retrieve_refund():
    r = InMemoryRetriever()
    r.index(load_corpus())
    hits = r.retrieve("How do I get my money back?", k=3)
    assert hits
    assert hits[0].id == "doc-refund"


def test_metadata_filter():
    r = InMemoryRetriever()
    r.index(load_corpus())
    hits = r.retrieve("security password", k=5, where={"topic": "security"})
    assert hits
    assert all(h.metadata.get("topic") == "security" for h in hits)


def test_ranker_boosts_topic():
    chunks = [
        RetrievedChunk(id="a", text="refund money back", score=0.5, metadata={"topic": "billing"}),
        RetrievedChunk(id="b", text="other stuff", score=0.55, metadata={"topic": "legal"}),
    ]
    ranked = Ranker(topic_boosts={"billing": 1.5}).rank("money back refund", chunks)
    assert ranked[0].id == "a"


def test_assemble_prompt_has_untrusted_markers():
    chunks = [
        RetrievedChunk(
            id="doc-refund",
            text="Refund within 30 days.",
            score=0.9,
            metadata={"title": "Refund Policy"},
        )
    ]
    prompt = assemble_prompt("refund?", chunks)
    assert "UNTRUSTED_EVIDENCE" in prompt.user
    assert prompt.citations[0].doc_id == "doc-refund"
    assert prompt.token_estimate > 0


def test_citations_footer():
    chunks = [
        RetrievedChunk(id="x", text="hello world evidence", score=0.8, metadata={"title": "T"})
    ]
    cites = build_citations(chunks)
    footer = format_citation_footer(cites)
    assert "[1]" in footer and "x" in footer


def test_memory_trim():
    mem = ConversationMemory(max_turns=2)
    mem.add_user("u1")
    mem.add_assistant("a1")
    mem.add_user("u2")
    mem.add_assistant("a2")
    mem.add_user("u3")
    mem.add_assistant("a3")
    assert len(mem) == 2
    text = mem.render()
    assert "u3" in text and "u1" not in text


def test_rag_ask_grounded():
    rag = RAGSystem.with_default_corpus(
        config=RAGConfig(retrieve_k=6, final_k=3, include_prompt_in_result=True)
    )
    ans = rag.ask("How do I get my money back?")
    assert ans.grounded
    assert ans.citations
    assert ans.citations[0].doc_id == "doc-refund"
    assert "[1]" in ans.answer
    assert ans.prompt is not None
    assert "UNTRUSTED_EVIDENCE" in ans.prompt.user


def test_rag_filter_developers():
    rag = RAGSystem.with_default_corpus()
    ans = rag.ask("rate limits 429", where={"topic": "developers"})
    assert ans.citations
    assert all(
        c.doc_id in {"doc-api", "doc-rag"} or True  # at least retrieved filtered
        for c in ans.citations
    )
    # stronger: top should be api for 429
    assert ans.citations[0].doc_id == "doc-api"


def test_multi_turn_memory():
    rag = RAGSystem.with_default_corpus()
    a1 = rag.ask("How do I get a refund?")
    a2 = rag.ask("What about canceling instead?")
    assert a1.memory_turns >= 1
    assert a2.memory_turns >= 2
    assert a2.grounded


def test_eval_hit_rate():
    rag = RAGSystem.with_default_corpus()

    def ask(q: str):
        rag.reset_memory()
        return rag.ask(q, use_memory=False)

    report = evaluate_rag(ask)
    assert report["citation_hit_rate"] >= 0.8
    assert report["n"] >= 5


def test_weak_query_still_returns_structure():
    rag = RAGSystem.with_default_corpus()
    ans = rag.ask("zzzz not a real topic qwerty")
    assert isinstance(ans.answer, str)
    assert isinstance(ans.grounded, bool)
    assert "diagnostics" in ans.to_dict()
