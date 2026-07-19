"""Tests for Chapter 11 prompt library."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from promptlib.patterns import (
    constraints_block,
    few_shot_pair,
    reasoning_instruction,
    role_preamble,
    untrusted_context_block,
)
from promptlib.registry import PromptRegistry, default_library_path
from promptlib.template import TemplateError, build_few_shot, build_zero_shot, render_prompt
from promptlib.testing import PromptTestSuite
from promptlib.types import FewShotExample, PromptSpec


@pytest.fixture
def registry() -> PromptRegistry:
    return PromptRegistry.from_directory(default_library_path())


def test_library_loads(registry: PromptRegistry):
    rows = registry.list()
    ids = {r["id"] for r in rows}
    assert "support.refund" in ids
    assert "extract.fields" in ids


def test_render_support_refund(registry: PromptRegistry):
    rendered = registry.render(
        "support.refund",
        {
            "role_line": role_preamble("a support agent", mission="help with refunds"),
            "company": "Acme",
            "context": "Refunds allowed within 30 days.",
            "question": "Can I get a refund after 45 days?",
        },
    )
    assert rendered.prompt_id == "support.refund"
    assert rendered.messages[0].role == "system"
    assert "30 days" in rendered.messages[-1].content
    assert "Never invent order IDs" in rendered.messages[0].content


def test_missing_vars_fail(registry: PromptRegistry):
    with pytest.raises(TemplateError):
        registry.render("support.refund", {"company": "Acme"})


def test_few_shot_extract_roles(registry: PromptRegistry):
    rendered = registry.render("extract.fields", {"message": "Order Z-9 is late"})
    roles = [m.role for m in rendered.messages]
    # system + (user,assistant)*2 + user
    assert roles[0] == "system"
    assert roles.count("user") >= 3
    assert roles.count("assistant") == 2
    assert rendered.messages[-1].content.endswith("Order Z-9 is late") or "Order Z-9" in rendered.messages[-1].content


def test_static_suite_passes(registry: PromptRegistry):
    report = PromptTestSuite(registry).run()
    assert report.passed, report.to_dict()


def test_high_risk_requires_constraints():
    bad = PromptSpec(
        id="x.bad",
        version="1.0.0",
        system="You are helpful.",
        user_template="{{q}}",
        required_vars=("q",),
        risk="high",
        constraints=(),
    )
    reg = PromptRegistry()
    reg.register(bad)
    report = PromptTestSuite(reg).run()
    assert report.passed is False
    assert any("high_risk_constraints" in r.name and not r.ok for r in report.results)


def test_pattern_helpers():
    assert "senior SRE" in role_preamble("a senior SRE", mission="reduce MTTR")
    assert "Hard constraints" in constraints_block(["Never invent IDs"])
    assert "UNTRUSTED_CONTEXT" in untrusted_context_block("hello")
    assert "final answer" in reasoning_instruction(mode="private_then_answer")
    ex = few_shot_pair("u", "a")
    assert ex.user == "u" and ex.assistant == "a"


def test_ad_hoc_builders():
    z = build_zero_shot(system="sys", user="do thing", constraints=["no invent"])
    assert z[0].role == "system" and "no invent" in z[0].content
    f = build_few_shot(
        system="sys",
        examples=[FewShotExample(user="u1", assistant="a1")],
        user="u2",
    )
    assert [m.role for m in f] == ["system", "user", "assistant", "user"]
