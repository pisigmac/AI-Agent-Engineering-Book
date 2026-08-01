import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import SupportAgent, KnowledgeBase, MockLLM


def test_resolve_from_kb():
    kb = KnowledgeBase(articles=[{"id": "1", "title": "Reset password", "body": "Click reset link"}])
    agent = SupportAgent(kb=kb, llm=MockLLM())
    t = agent.open_ticket("u", "reset password please")
    r = agent.handle(t.id)
    assert r["status"] == "resolved"
    assert r["reply"]


def test_escalate():
    agent = SupportAgent(kb=KnowledgeBase(), llm=MockLLM())
    t = agent.open_ticket("u", "I will call my lawyer")
    r = agent.handle(t.id)
    assert r["escalated"] is True
