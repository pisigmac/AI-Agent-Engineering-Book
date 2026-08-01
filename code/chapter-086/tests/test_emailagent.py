import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from emailagent import Email, EmailAgent, MockLLM, MockMailbox


def test_triage_order_and_spam():
    box = MockMailbox(inbox=[
        Email("1", "a@x.com", "hello", "intro meet"),
        Email("2", "b@x.com", "URGENT outage", "down"),
        Email("3", "s@x.com", "Lottery", "prince lottery"),
    ])
    agent = EmailAgent(mailbox=box, llm=MockLLM())
    t = agent.triage()
    assert t[0]["id"] == "2"
    assert any(r["spam"] for r in t)


def test_draft_skips_spam():
    box = MockMailbox(inbox=[Email("3", "s@x.com", "Lottery", "prince lottery")])
    agent = EmailAgent(mailbox=box, llm=MockLLM())
    d = agent.draft_reply("3")
    assert d.get("skipped") is True
