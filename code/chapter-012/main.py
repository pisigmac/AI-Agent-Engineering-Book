"""Chapter 12 CLI — context assembly demos."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from contextkit.manager import AssemblyError, ContextManager
from contextkit.types import (
    ContextState,
    HistoryTurn,
    MemoryHit,
    Priority,
    ToolResult,
)


def _load_state(path: Path) -> ContextState:
    raw = json.loads(path.read_text(encoding="utf-8"))
    history = [
        HistoryTurn(
            role=h["role"],
            content=h["content"],
            turn_id=h.get("turn_id"),
            priority=Priority(h.get("priority", "normal")),
        )
        for h in raw.get("history") or []
    ]
    tools = [
        ToolResult(
            call_id=t["call_id"],
            name=t["name"],
            content=t["content"],
            priority=Priority(t.get("priority", "normal")),
        )
        for t in raw.get("tools") or []
    ]
    memories = [
        MemoryHit(
            memory_id=m["memory_id"],
            content=m["content"],
            score=float(m.get("score") or 0.0),
            source=str(m.get("source") or ""),
            priority=Priority(m.get("priority", "high")),
        )
        for m in raw.get("memories") or []
    ]
    return ContextState(
        system_policy=raw["system_policy"],
        goal=str(raw.get("goal") or ""),
        history=history,
        tools=tools,
        memories=memories,
        policy_id=raw.get("policy_id"),
    )


def cmd_assemble(fixture: Path, budget: int, max_tool: int) -> int:
    state = _load_state(fixture)
    manager = ContextManager(max_tokens_tool=max_tool, max_tokens_memory=500)
    try:
        result = manager.assemble(state, budget=budget)
    except AssemblyError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        return 1
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_compare(fixture: Path) -> int:
    state = _load_state(fixture)
    manager = ContextManager(max_tokens_tool=400, max_tokens_memory=300)
    rows = []
    for budget in (350, 700, 2000):
        try:
            result = manager.assemble(state, budget=budget)
            rows.append(
                {
                    "budget": budget,
                    "tokens_est": result.report.tokens_est,
                    "kept": result.report.kept_ids,
                    "dropped": result.report.dropped_ids,
                    "compressed": result.report.compressed_ids,
                    "ok": not result.report.over_budget,
                }
            )
        except AssemblyError as exc:
            rows.append({"budget": budget, "error": str(exc)})
    print(json.dumps({"comparisons": rows}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 12 — context manager CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_as = sub.add_parser("assemble", help="Assemble context from a fixture")
    p_as.add_argument("--fixture", type=Path, required=True)
    p_as.add_argument("--budget", type=int, default=800)
    p_as.add_argument("--max-tool-tokens", type=int, default=600)

    p_cmp = sub.add_parser("compare", help="Compare assembly across budgets")
    p_cmp.add_argument("--fixture", type=Path, required=True)

    args = parser.parse_args(argv)
    if args.cmd == "assemble":
        return cmd_assemble(args.fixture, args.budget, args.max_tool_tokens)
    if args.cmd == "compare":
        return cmd_compare(args.fixture)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
