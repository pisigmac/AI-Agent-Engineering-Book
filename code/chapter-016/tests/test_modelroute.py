"""Tests for model catalog, routing, and fallback completion."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modelroute.catalog import default_catalog
from modelroute.classifier import build_task_request, estimate_tokens, infer_task_kind
from modelroute.completer import MockBackend, RoutedCompleter, build_default_completer
from modelroute.matrix import strategy_matrix
from modelroute.router import ModelRouter, NoEligibleModelError
from modelroute.scoring import eligibility, score_model
from modelroute.types import (
    QualityTier,
    RouteStrategy,
    TaskKind,
    TaskRequest,
)


def test_catalog_has_major_providers():
    cats = default_catalog()
    providers = {p.provider.value for p in cats}
    assert {"openai", "anthropic", "google", "meta", "mistral"} <= providers
    assert any(p.capabilities.open_weights for p in cats)
    assert any(p.capabilities.embeddings for p in cats)


def test_infer_task_kinds():
    assert infer_task_kind("Classify intent: billing") is TaskKind.CLASSIFY
    assert infer_task_kind("Summarize this transcript") is TaskKind.SUMMARIZE
    assert infer_task_kind("Refactor this python function") is TaskKind.CODE
    assert infer_task_kind("Use the get_weather tool") is TaskKind.TOOL_PLAN
    assert infer_task_kind("Prove multi-hop architecture trade-off carefully") is TaskKind.REASONING


def test_cost_strategy_prefers_cheaper_for_classify():
    router = ModelRouter()
    task = build_task_request("Classify intent: billing")
    d = router.route(task, strategy=RouteStrategy.COST)
    # Should not pick flagship for trivial classify under cost strategy
    assert "flagship" not in d.selected_model_id
    cost = router.get(d.selected_model_id).estimated_cost_usd(
        task.expected_input_tokens, task.expected_output_tokens
    )
    flagship = router.get("openai:gpt-flagship").estimated_cost_usd(
        task.expected_input_tokens, task.expected_output_tokens
    )
    assert cost <= flagship


def test_quality_strategy_escalates_reasoning():
    router = ModelRouter()
    task = build_task_request(
        "Prove multi-hop architecture trade-off carefully step by step"
    )
    d = router.route(task, strategy=RouteStrategy.QUALITY)
    profile = router.get(d.selected_model_id)
    assert profile.quality in {QualityTier.LARGE, QualityTier.FLAGSHIP}


def test_tools_requirement_filters_embed_only():
    router = ModelRouter()
    task = TaskRequest(
        kind=TaskKind.TOOL_PLAN,
        prompt="call tool get_weather",
        require_tools=True,
    )
    ranked = router.rank(task, strategy=RouteStrategy.BALANCED)
    embed = next(c for c in ranked if c.model.model_id == "local:embed-mini")
    assert not embed.eligible
    assert any(c.eligible and c.model.capabilities.tools for c in ranked)


def test_pinned_model():
    router = ModelRouter()
    task = build_task_request("hello", pinned_model_id="mistral:small")
    d = router.route(task, strategy=RouteStrategy.PINNED)
    assert d.selected_model_id == "mistral:small"


def test_no_eligible_raises():
    router = ModelRouter()
    # Impossible combo: flagship quality + near-zero budget + vision
    task = TaskRequest(
        kind=TaskKind.CHAT,
        prompt="hi",
        min_quality=QualityTier.FLAGSHIP,
        max_cost_usd=1e-9,
        require_vision=True,
    )
    with pytest.raises(NoEligibleModelError):
        router.route(task)


def test_fallback_on_primary_failure():
    router = ModelRouter()
    task = build_task_request("Classify intent: billing")
    decision = router.route(task, strategy=RouteStrategy.COST)
    primary = decision.selected_model_id
    assert len(decision.fallback_chain) >= 2
    backend = MockBackend(fail_models={primary})
    completer = RoutedCompleter(
        router=router, backend=backend, default_strategy=RouteStrategy.COST
    )
    result = completer.complete(task, strategy=RouteStrategy.COST)
    assert result.fallback_used
    assert result.model_id != primary
    assert result.attempts[0]["ok"] is False
    assert result.attempts[0]["model_id"] == primary


def test_complete_happy_path():
    c = build_default_completer(strategy=RouteStrategy.BALANCED)
    r = c.complete(build_task_request("hello there"))
    assert r.text
    assert r.model_id
    assert r.cost_usd >= 0
    assert r.latency_ms > 0


def test_strategy_matrix_keys():
    router = ModelRouter()
    task = build_task_request("Summarize the meeting notes")
    m = strategy_matrix(router, task)
    assert set(m["strategies"]) >= {"cost", "latency", "quality", "balanced"}


def test_score_monotonic_quality_for_same_cost_bucket():
    router = ModelRouter()
    task = TaskRequest(kind=TaskKind.CHAT, prompt="x" * 40, expected_input_tokens=100, expected_output_tokens=50)
    small = router.get("openai:gpt-fast")
    flag = router.get("openai:gpt-flagship")
    s_small = score_model(small, task, RouteStrategy.QUALITY)
    s_flag = score_model(flag, task, RouteStrategy.QUALITY)
    assert s_flag.total > s_small.total


def test_estimate_tokens():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1


def test_eligibility_context_window():
    router = ModelRouter()
    local = router.get("meta:llama-local-8b")
    task = TaskRequest(
        kind=TaskKind.CHAT,
        prompt="long",
        expected_input_tokens=50_000,
        expected_output_tokens=1000,
    )
    ok, reasons = eligibility(local, task)
    assert not ok
    assert "context_window_too_small" in reasons
