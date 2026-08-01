#!/usr/bin/env python3
import json
from research import ResearchAgent, MockSearch, MockLLM


def main() -> int:
    search = MockSearch(
        corpus=[
            {"title": "Agents 101", "url": "u1", "snippet": "AI agents plan and use tools."},
            {"title": "Risks", "url": "u2", "snippet": "Agent risks include runaway actions."},
            {"title": "Benefits", "url": "u3", "snippet": "Agents automate research workflows."},
        ]
    )
    agent = ResearchAgent(search=search, llm=MockLLM())
    report = agent.run("AI agents")
    print(json.dumps({
        "topic": report.topic,
        "subqs": report.subquestions,
        "sources": len(report.sources),
        "synthesis": report.synthesis[:200],
        "events": len(report.events),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
