#!/usr/bin/env python3
import json
from portfolio import Project, Portfolio, Contribution


def main() -> int:
    folio = Portfolio()
    folio.add_project(
        Project(
            name="support-agent",
            url="https://github.com/you/support-agent",
            tags=["agents", "rag"],
            readme_flags={k: True for k in [
                "problem_statement", "architecture_diagram", "quickstart", "tests", "license", "demo_or_screenshots"
            ]},
            has_tests=True,
            has_ci=True,
            has_docker=True,
            stars=12,
            production_used=False,
        )
    )
    folio.add_project(
        Project(
            name="toy-bot",
            url="https://github.com/you/toy-bot",
            readme_flags={"quickstart": True},
            has_tests=False,
        )
    )
    folio.add_contribution(Contribution("langchain", "docs", "Fix tool calling example", merged=True))
    print(json.dumps(folio.report(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
