import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from meeting import MeetingAssistant, Transcript, MockLLM


def test_extract():
    t = Transcript("m1", "Plan", [
        "Ada: Decided to ship v1.",
        "Bob will write tests by Monday.",
        "ACTION: Ada: merge PR",
    ])
    r = MeetingAssistant(llm=MockLLM()).process(t)
    assert r["decisions"]
    assert len(r["action_items"]) >= 2
    assert r["summary"]
