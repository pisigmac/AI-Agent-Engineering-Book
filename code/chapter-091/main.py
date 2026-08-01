#!/usr/bin/env python3
import json
from sysdesign import SystemDesignKit, LatencyBudget


def main() -> int:
    kit = SystemDesignKit(title="Multi-tenant support agent")
    kit.checklist.mark("Clarify requirements and non-goals")
    kit.checklist.mark("Estimate scale (QPS, storage, cost)")
    budget = LatencyBudget(
        total_ms=3000,
        parts={"auth": 50, "retrieve": 200, "llm": 2000, "tools": 400, "post": 50},
    )
    print(json.dumps(kit.brief(
        dau=100_000,
        requests_per_user_day=2.0,
        avg_payload_kb=4.0,
        latency=budget,
    ), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
