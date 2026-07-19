"""Tests for Chapter 8 LLM concept lab."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from llm_concepts.eval_basic import evaluate_answer
from llm_concepts.grounding import Document, GroundedQA, InMemoryDocStore, default_policy_corpus
from llm_concepts.mock_llm import MockLLM, MockMode
from llm_concepts.taxonomy import Capability, RiskClass, TrainingPhase, explain_llm


def test_explain_taxonomy():
    data = explain_llm()
    assert "definition" in data
    assert len(data["phases"]) == 3
    assert {p["phase"] for p in data["phases"]} == {p.value for p in TrainingPhase}
    assert len(data["capabilities"]) == len(Capability)
    assert len(data["risks"]) == len(RiskClass)


def test_mock_echo_and_hallucinate():
    echo = MockLLM(mode=MockMode.ECHO).complete("hello")
    assert echo.text.startswith("ECHO:")
    assert echo.grounded is False

    hallu = MockLLM(mode=MockMode.HALLUCINATE).complete("refund policy")
    assert "99-ZZZ" in hallu.text
    assert hallu.grounded is False


def test_grounded_answers_from_docs():
    qa = GroundedQA(default_policy_corpus())
    result, docs = qa.ask("What is the refund window?")
    assert docs
    assert "30" in result.text
    assert result.grounded is True


def test_grounded_refuses_without_evidence():
    store = InMemoryDocStore(
        [Document("a", "A", "The office plants are watered weekly.")]
    )
    result, _ = GroundedQA(store).ask("What is the refund window?")
    assert result.grounded is False
    assert "does not contain" in result.text.lower() or "supporting context" in result.text.lower()


def test_eval_flags_hallucination():
    hallu = MockLLM(mode=MockMode.HALLUCINATE).complete("refunds")
    report = evaluate_answer(hallu)
    assert report.passed is False
    assert any(i.code == "fake_citation_pattern" for i in report.issues)


def test_eval_passes_grounded_refund_answer():
    qa = GroundedQA(default_policy_corpus())
    result, docs = qa.ask("What is the refund window?")
    ctx = "\n".join(d.text for d in docs)
    report = evaluate_answer(result, context=ctx, expect_grounded=True)
    assert report.passed is True


def test_eval_accepts_refusal_when_unanswerable():
    store = InMemoryDocStore([Document("x", "X", "Only talks about office plants.")])
    result, docs = GroundedQA(store).ask("Who is the CEO?")
    ctx = "\n".join(d.text for d in docs)
    report = evaluate_answer(result, context=ctx, expect_grounded=True)
    assert "refusal_detected" in report.notes
