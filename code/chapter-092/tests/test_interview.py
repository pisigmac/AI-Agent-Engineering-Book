import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from interview import InterviewBank, MockInterview, score_answer


def test_score_pass():
    q = InterviewBank().get("ag1")
    r = score_answer(
        q,
        "First, use an allowlist and sandbox execution. Second, require "
        "human-in-the-loop approval with policy gates and a full audit trail.",
    )
    assert r["passed"] is True


def test_score_fail_short():
    q = InterviewBank().get("ag1")
    r = score_answer(q, "be careful")
    assert r["passed"] is False


def test_mock_summary():
    m = MockInterview(bank=InterviewBank())
    m.ask("be1", "Impact was outage. Root cause was bad deploy. Timeline 30m. Fix rollback. Prevention canary.")
    s = m.summary()
    assert s["n"] == 1
    assert 0 <= s["pass_rate"] <= 1
