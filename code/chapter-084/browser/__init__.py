"""Browser Agent — navigate, extract, act via tool interface (mocked DOM)."""
from .agent import BrowserAgent, MockBrowser, MockLLM, Page

__all__ = ["BrowserAgent", "MockBrowser", "MockLLM", "Page"]
__version__ = "1.0.0"
