#!/usr/bin/env python3
import json
from browser import BrowserAgent, MockBrowser, MockLLM, Page


def main() -> int:
    pages = {
        "https://ex.com": Page("https://ex.com", "Home", "Welcome", {"Pricing": "https://ex.com/pricing"}),
        "https://ex.com/pricing": Page("https://ex.com/pricing", "Pricing", "Pro plan $20/mo", {}),
    }
    agent = BrowserAgent(browser=MockBrowser(pages=pages), llm=MockLLM())
    out = agent.run("https://ex.com", "Find pricing")
    print(json.dumps({k: out[k] for k in ("goal", "answer", "history")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
