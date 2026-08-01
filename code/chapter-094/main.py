#!/usr/bin/env python3
import json
from career import StartupGuide


def main() -> int:
    guide = StartupGuide.default_track()
    guide.canvas.problem = ["Support tickets overwhelm SMBs"]
    guide.canvas.customer_segments = ["B2B SaaS under 200 employees"]
    guide.canvas.unique_value = "Agent that resolves L1 with eval gates"
    guide.canvas.solution = ["KB RAG", "ticket tools", "escalation policy"]
    guide.canvas.key_metrics = ["resolution rate", "cost per ticket"]
    guide.roadmap.complete("m1")
    print(json.dumps(guide.snapshot(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
