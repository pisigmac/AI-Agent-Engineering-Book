"""Agent evaluation: task success, tool correctness, regression suite."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable

AgentFn = Callable[[str], dict[str, Any]]

@dataclass
class Case:
    id: str
    goal: str
    expect_ok: bool = True
    expect_contains: tuple[str, ...] = ()
    expect_tools: tuple[str, ...] = ()

def evaluate(agent: AgentFn, cases: list[Case]) -> dict[str, Any]:
    rows = []
    passed = 0
    for case in cases:
        out = agent(case.goal)
        ok = bool(out.get("ok", True))
        text = str(out.get("result", ""))
        tools = list(out.get("tools_used") or [])
        checks = {
            "ok_match": ok == case.expect_ok,
            "contains": all(s.lower() in text.lower() for s in case.expect_contains),
            "tools": all(t in tools for t in case.expect_tools),
        }
        success = all(checks.values())
        if success:
            passed += 1
        rows.append({"id": case.id, "success": success, "checks": checks, "result": text[:120]})
    n = max(len(cases), 1)
    return {"n": len(cases), "pass_rate": round(passed / n, 4), "passed": passed, "rows": rows}

def demo_agent(goal: str) -> dict[str, Any]:
    g = goal.lower()
    if "weather" in g:
        return {"ok": True, "result": "Berlin: 18C cloudy", "tools_used": ["weather"]}
    if "refund" in g:
        return {"ok": True, "result": "Refunds within 30 days", "tools_used": ["policy"]}
    return {"ok": False, "result": "unknown", "tools_used": []}

DEFAULT_CASES = [
    Case("weather", "weather in Berlin", expect_contains=("18C",), expect_tools=("weather",)),
    Case("refund", "refund policy", expect_contains=("30",), expect_tools=("policy",)),
    Case("fail", "unrelated xyz", expect_ok=False),
]
