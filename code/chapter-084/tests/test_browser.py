import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from browser import BrowserAgent, MockBrowser, MockLLM, Page


def test_navigate_to_pricing():
    pages = {
        "https://ex.com": Page("https://ex.com", "Home", "Welcome", {"Pricing": "https://ex.com/pricing"}),
        "https://ex.com/pricing": Page("https://ex.com/pricing", "Pricing", "Pro plan $20/mo", {}),
    }
    agent = BrowserAgent(browser=MockBrowser(pages=pages), llm=MockLLM())
    out = agent.run("https://ex.com", "Find pricing")
    assert "https://ex.com/pricing" in out["history"]
    assert out["answer"]


def test_404():
    b = MockBrowser(pages={})
    with pytest.raises(KeyError):
        b.goto("https://missing")
