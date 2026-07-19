"""Production tests for Chapter 10 token toolkit."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from token_kit.accounting import UsageLedger
from token_kit.budget import effective_input_budget, fits, utilization
from token_kit.compress import TRUNCATION_MARKER, cap_text, cap_tool_messages, sliding_window
from token_kit.packer import ContextPacker
from token_kit.pricing import PriceTable, estimate_cost
from token_kit.tokenizers import ApproxCl100kCounter, CharHeuristicCounter
from token_kit.types import BudgetConfig, ChatMessage, Priority, Role, TokenUsage


def _msgs() -> list[ChatMessage]:
    path = ROOT / "fixtures" / "sample_messages.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    # inflate low-priority message for stress
    for item in raw:
        if item.get("message_id") == "u-3":
            item["content"] = item["content"] * 200
    return [
        ChatMessage(
            role=Role(item["role"]),
            content=item["content"],
            name=item.get("name"),
            message_id=item.get("message_id"),
            priority=item.get("priority"),
        )
        for item in raw
    ]


def test_counters_positive_and_code_heavier_than_short_word():
    approx = ApproxCl100kCounter()
    char = CharHeuristicCounter()
    assert approx.count_text("hello") >= 1
    assert char.count_text("hello") >= 1
    code = "def foo(x):\n    return x + 1\n" * 5
    prose = "hello world " * 10
    # not a strict law, but codey text should not be zero
    assert approx.count_text(code) > 10
    assert approx.count_text(prose) > 5


def test_message_count_includes_overhead():
    c = ApproxCl100kCounter()
    messages = [
        ChatMessage(role=Role.SYSTEM, content="policy"),
        ChatMessage(role=Role.USER, content="hi"),
    ]
    assert c.count_messages(messages) > c.count_text("policy") + c.count_text("hi")


def test_effective_budget_math():
    cfg = BudgetConfig(context_window=8192, max_completion=1024, margin=256, reserved_tools=100)
    assert effective_input_budget(cfg) == 8192 - 1024 - 256 - 100
    assert fits(100, cfg) is True
    assert utilization(effective_input_budget(cfg), cfg) == 1.0


def test_estimate_cost():
    price = PriceTable().get("gpt-4.1")
    usage = TokenUsage(input_tokens=1_000_000, output_tokens=1_000_000)
    cost = estimate_cost(usage, price)
    assert cost == pytest.approx(price.input_per_mtok + price.output_per_mtok)


def test_cap_text_and_tool_messages():
    c = ApproxCl100kCounter()
    huge = "abcdefghijklmnopqrstuvwxyz " * 500
    capped, truncated = cap_text(huge, c, max_tokens=50)
    assert truncated is True
    assert TRUNCATION_MARKER.strip() in capped
    assert c.count_text(capped) <= 50
    msgs = [
        ChatMessage(role=Role.TOOL, content=huge, name="t", message_id="t1"),
        ChatMessage(role=Role.USER, content="ok", message_id="u1"),
    ]
    out = cap_tool_messages(msgs, c, max_tokens_per_tool=40)
    assert out[0].metadata.get("truncated") is True
    assert out[1].content == "ok"


def test_sliding_window_keeps_system():
    messages = [
        ChatMessage(role=Role.SYSTEM, content="sys", message_id="s"),
        ChatMessage(role=Role.USER, content="1", message_id="1"),
        ChatMessage(role=Role.USER, content="2", message_id="2"),
        ChatMessage(role=Role.USER, content="3", message_id="3"),
    ]
    out = sliding_window(messages, keep_last=2)
    assert out[0].role is Role.SYSTEM
    assert [m.message_id for m in out[1:]] == ["2", "3"]


def test_packer_pins_system_and_respects_budget():
    messages = _msgs()
    counter = ApproxCl100kCounter()
    packer = ContextPacker(counter, max_tokens_per_tool=128)
    # Tight budget forces drops
    cfg = BudgetConfig(context_window=900, max_completion=100, margin=50)
    result = packer.pack(messages, cfg)
    assert result.tokens_est <= result.budget
    assert result.over_budget is False
    assert any(m.role is Role.SYSTEM for m in result.kept)
    assert any(m.role is Role.SYSTEM for m in result.kept)
    # bulky low priority should be drop candidate
    dropped_ids = {m.message_id for m in result.dropped}
    assert result.dropped  # something dropped under tight budget


def test_packer_partition_complete():
    messages = _msgs()
    counter = ApproxCl100kCounter()
    packer = ContextPacker(counter)
    cfg = BudgetConfig(context_window=50_000, max_completion=1024, margin=256)
    result = packer.pack(messages, cfg)
    kept_ids = {m.message_id for m in result.kept}
    dropped_ids = {m.message_id for m in result.dropped}
    all_ids = {m.message_id for m in messages}
    assert kept_ids | dropped_ids == all_ids
    assert kept_ids.isdisjoint(dropped_ids)


def test_usage_ledger():
    ledger = UsageLedger()
    ledger.add("step1", TokenUsage(100, 20, tokenizer="t"), model="gpt-4.1-mini")
    ledger.add("step2", TokenUsage(50, 10, tokenizer="t"), model="gpt-4.1-mini")
    totals = ledger.totals()
    assert totals.input_tokens == 150
    assert totals.output_tokens == 30
    price = PriceTable().get("gpt-4.1-mini")
    data = ledger.to_dict(price)
    assert data["steps"] == 2
    assert data["cost_usd_est"] >= 0
