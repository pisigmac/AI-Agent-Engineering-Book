#!/usr/bin/env python3
import json
from emailagent import Email, EmailAgent, MockLLM, MockMailbox


def main() -> int:
    box = MockMailbox(inbox=[
        Email("1", "a@x.com", "URGENT outage", "API is down"),
        Email("2", "b@x.com", "Invoice question", "About payment"),
        Email("3", "spam@x.com", "Lottery winner", "prince lottery"),
    ])
    agent = EmailAgent(mailbox=box, llm=MockLLM())
    triage = agent.triage()
    draft = agent.draft_reply("1")
    print(json.dumps({"triage": triage, "draft": draft}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
