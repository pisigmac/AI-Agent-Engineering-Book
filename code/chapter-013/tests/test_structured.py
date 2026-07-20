"""Tests for structured output pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from structured.complete import StructuredCompleter
from structured.extract import extract_json_object
from structured.mock_llm import MockLLM
from structured.schema_models import Intent, RefundAssessment, RouteDecision
from structured.types import StructureParseError, StructureValidationError
from structured.validate import validate_model


def test_extract_pure_and_fenced():
    assert extract_json_object('{"a": 1}') == {"a": 1}
    fenced = """Here you go:
```json
{"intent": "refund", "confidence": 0.9}
```
thanks"""
    assert extract_json_object(fenced)["intent"] == "refund"


def test_extract_embedded_object():
    text = 'prefix {"order_id":"A-1","ok":true} suffix'
    assert extract_json_object(text)["order_id"] == "A-1"


def test_extract_rejects_empty_and_array():
    with pytest.raises(StructureParseError):
        extract_json_object("   ")
    with pytest.raises(StructureParseError):
        extract_json_object("[1,2,3]")


def test_validate_route_decision():
    model = validate_model(
        RouteDecision,
        {
            "intent": "billing",
            "confidence": 0.7,
            "needs_human": False,
            "rationale": "Mentions invoice",
        },
    )
    assert model.intent is Intent.BILLING


def test_validate_rejects_confidence_out_of_range():
    with pytest.raises(StructureValidationError) as exc:
        validate_model(
            RouteDecision,
            {
                "intent": "shipping",
                "confidence": 1.5,
                "needs_human": False,
                "rationale": "pkg",
            },
        )
    assert exc.value.errors


def test_completer_repairs_invalid_then_succeeds():
    llm = MockLLM(
        script=[
            (
                "validation",
                json.dumps(
                    {
                        "intent": "shipping",
                        "confidence": 0.91,
                        "needs_human": False,
                        "rationale": "Mentions package tracking.",
                    }
                ),
            ),
            (
                "package",
                json.dumps(
                    {
                        "intent": "shipping",
                        "confidence": 4.0,
                        "needs_human": False,
                        "rationale": "package",
                    }
                ),
            ),
        ]
    )
    completer = StructuredCompleter(llm.generate, max_repairs=2)
    result = completer.complete(
        [
            {"role": "system", "content": "Classify. JSON only."},
            {"role": "user", "content": "Where is my package?"},
        ],
        RouteDecision,
    )
    assert result.ok
    assert result.value is not None
    assert result.value.intent is Intent.SHIPPING
    assert 0.0 <= result.value.confidence <= 1.0
    assert len(result.attempts) == 2
    assert result.attempts[0].ok is False
    assert result.attempts[1].ok is True


def test_completer_exhausted():
    llm = MockLLM(default="not json at all")
    completer = StructuredCompleter(llm.generate, max_repairs=1)
    result = completer.complete(
        [{"role": "user", "content": "hello"}],
        RouteDecision,
    )
    assert not result.ok
    assert result.error is not None
    assert result.error.code == "repairs_exhausted"


def test_refund_model_and_fixture_path():
    doc = (ROOT / "fixtures" / "order_note.txt").read_text(encoding="utf-8")
    assert "A-100" in doc
    model = validate_model(
        RefundAssessment,
        {
            "decision": "deny",
            "order_id": "A-100",
            "reason_code": "outside_window",
            "evidence": ["45 days ago", "within 30 days"],
            "needs_human": False,
            "confidence": 0.8,
        },
    )
    assert model.decision == "deny"
