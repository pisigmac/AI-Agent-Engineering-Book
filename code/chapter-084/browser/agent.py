"""Browser automation agent over a mock page graph (no real network)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
import re


@dataclass
class Page:
    url: str
    title: str
    text: str
    links: dict[str, str] = field(default_factory=dict)  # label -> url


@dataclass
class MockBrowser:
    pages: dict[str, Page]
    current: str | None = None
    history: list[str] = field(default_factory=list)

    def goto(self, url: str) -> Page:
        if url not in self.pages:
            raise KeyError(f"404: {url}")
        self.current = url
        self.history.append(url)
        return self.pages[url]

    def extract(self, selector: str = "body") -> str:
        if not self.current:
            raise RuntimeError("no page loaded")
        page = self.pages[self.current]
        if selector == "title":
            return page.title
        if selector.startswith("link:"):
            label = selector[5:]
            return page.links.get(label, "")
        return page.text

    def click(self, label: str) -> Page:
        if not self.current:
            raise RuntimeError("no page loaded")
        page = self.pages[self.current]
        if label not in page.links:
            raise KeyError(f"no link: {label}")
        return self.goto(page.links[label])


class LLM(Protocol):
    def decide(self, goal: str, observation: str, steps_left: int) -> dict[str, Any]: ...


@dataclass
class MockLLM:
    """Heuristic policy for demos/tests."""

    def decide(self, goal: str, observation: str, steps_left: int) -> dict[str, Any]:
        g = goal.lower()
        obs = observation.lower()
        # Done only when we are on a pricing page with price-like content
        if "pricing" in g and ("/pricing" in obs or "$" in observation or "plan" in obs and "pro" in obs):
            return {"action": "done", "answer": observation[:300]}
        if "pricing" in g:
            if "Pricing" in observation or "pricing" in obs:
                return {"action": "click", "target": "Pricing"}
            return {"action": "extract", "selector": "body"}
        if "done" in g or steps_left <= 1:
            return {"action": "done", "answer": observation[:200]}
        return {"action": "extract", "selector": "body"}


@dataclass
class BrowserAgent:
    browser: MockBrowser
    llm: LLM
    max_steps: int = 6

    def run(self, start_url: str, goal: str) -> dict[str, Any]:
        events: list[dict[str, Any]] = []
        page = self.browser.goto(start_url)
        events.append({"type": "goto", "url": start_url})
        answer = ""
        for step in range(self.max_steps):
            obs = f"url={page.url} title={page.title} text={page.text[:200]} links={list(page.links)}"
            decision = self.llm.decide(goal, obs, self.max_steps - step)
            events.append({"type": "decide", "step": step, "decision": decision})
            act = decision.get("action")
            if act == "done":
                answer = str(decision.get("answer", ""))
                break
            if act == "goto":
                page = self.browser.goto(str(decision["url"]))
            elif act == "click":
                page = self.browser.click(str(decision["target"]))
            elif act == "extract":
                text = self.browser.extract(str(decision.get("selector", "body")))
                events.append({"type": "extract", "text": text[:200]})
                if goal.lower() in text.lower() or any(t in text.lower() for t in goal.lower().split()):
                    answer = text[:300]
                    break
            else:
                events.append({"type": "unknown_action", "decision": decision})
                break
        return {"goal": goal, "answer": answer, "history": list(self.browser.history), "events": events}
