#!/usr/bin/env python3
import json
from interview import InterviewBank, MockInterview


def main() -> int:
    mock = MockInterview(bank=InterviewBank())
    mock.ask(
        "ag1",
        "First, allowlist tools. Second, sandbox side effects. "
        "Add human-in-the-loop for risky actions, policy checks, and an audit log.",
    )
    mock.ask(
        "co1",
        "Use retry with exponential backoff and jitter; keep calls idempotent; set timeouts.",
    )
    print(json.dumps(mock.summary(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
