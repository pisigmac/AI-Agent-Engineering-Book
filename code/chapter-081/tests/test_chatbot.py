import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chatbot import ChatBot, MockLLM


def test_multi_turn():
    bot = ChatBot(llm=MockLLM(prefix="OK"))
    s = bot.new_session()
    r = bot.chat(s.session_id, "hi")
    assert r["reply"].startswith("OK")
    assert r["turns"] == 1
    bot.chat(s.session_id, "again")
    assert bot.chat(s.session_id, "third")["turns"] == 3


def test_unknown_session():
    bot = ChatBot(llm=MockLLM())
    with pytest.raises(KeyError):
        bot.chat("nope", "x")


def test_events():
    bot = ChatBot(llm=MockLLM())
    s = bot.new_session()
    bot.chat(s.session_id, "a")
    kinds = [e["type"] for e in bot.events.events]
    assert "session_start" in kinds
    assert "user_message" in kinds
