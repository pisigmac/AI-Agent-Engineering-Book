#!/usr/bin/env python3
import json
from support import SupportAgent, KnowledgeBase, MockLLM


def main() -> int:
    kb = KnowledgeBase(articles=[
        {"id": "kb1", "title": "Reset password", "body": "Use Settings > Security > Reset password link."},
        {"id": "kb2", "title": "API downtime", "body": "Check status page; incidents resolve within 1 hour SLA."},
    ])
    agent = SupportAgent(kb=kb, llm=MockLLM())
    t1 = agent.open_ticket("u1", "How do I reset password?")
    t2 = agent.open_ticket("u2", "I want to speak to manager about chargeback")
    print(json.dumps({"a": agent.handle(t1.id), "b": agent.handle(t2.id)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
