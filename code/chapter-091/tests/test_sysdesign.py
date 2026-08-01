import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sysdesign import estimate_capacity, LatencyBudget, DesignChecklist, SystemDesignKit


def test_capacity():
    c = estimate_capacity(dau=86_400, requests_per_user_day=1.0, avg_payload_kb=1.0, peak_multiplier=1.0)
    assert c.daily_requests == 86_400
    assert abs(c.qps - 1.0) < 1e-6


def test_latency_budget():
    b = LatencyBudget(total_ms=1000, parts={"a": 400, "b": 500})
    assert b.remaining() == 100
    assert b.valid()
    bad = LatencyBudget(total_ms=100, parts={"a": 80, "b": 30})
    assert not bad.valid()


def test_checklist_and_brief():
    kit = SystemDesignKit(title="X")
    kit.checklist.mark(kit.checklist.items[0])
    out = kit.brief(
        dau=1000,
        requests_per_user_day=1,
        avg_payload_kb=1,
        latency=LatencyBudget(1000, {"llm": 800}),
    )
    assert out["checklist"]["done"] == 1
    assert "capacity" in out


def test_negative():
    with pytest.raises(ValueError):
        estimate_capacity(dau=-1, requests_per_user_day=1, avg_payload_kb=1)
