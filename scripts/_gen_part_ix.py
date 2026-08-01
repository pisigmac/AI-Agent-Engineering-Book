#!/usr/bin/env python3
"""Generate Part IX — Real Projects (chapters 81–90). Offline-testable apps."""
from __future__ import annotations

import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip("\n") if content.startswith("\n") else content)
    if not content.endswith("\n"):
        path.write_text(path.read_text() + "\n")


# ---------------------------------------------------------------------------
# Shared helpers for each chapter package
# ---------------------------------------------------------------------------

def pyproject(n: int) -> str:
    return f"""[project]
name = "ai-agent-platform-chapter-{n:03d}"
version = "1.0.0"
requires-python = ">=3.10"
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
"""


def dockerfile(pkg: str) -> str:
    return f"""FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir pytest
ENV PYTHONPATH=/app
CMD ["python3", "main.py"]
# Health: python3 -c "from {pkg} import *; print('ok')"
"""


def readme(n: int, title: str, pkg: str) -> str:
    return f"""# Chapter {n:03d} — {title}

Production-style project package `{pkg}` (offline mocks for CI).

```bash
cd code/chapter-{n:03d} && pytest -q && python3 main.py
docker build -t ch{n:03d}-{pkg} .
```
"""


def book_md(n: int, title: str, pkg: str, summary: str, next_line: str) -> str:
    return f"""# Chapter {n}: {title}

## Chapter Overview

Part IX **Real Projects** — full application **{title}** implemented as package `{pkg}`.

Readers assemble platform modules from earlier parts into a deployable product slice: architecture, offline-testable core, Docker image, observability hooks, and scaling notes.

## Learning Objectives

- Design end-to-end architecture for a **{title}**
- Implement a production-shaped core with pure interfaces and offline mocks
- Add tests, Docker packaging, and basic observability
- Discuss deployment, scaling, and future improvements

## Prerequisites

Parts I–VIII (platform foundation, agents, systems, APIs, framework modules).

## Motivation

Theory without shipped products leaves a gap. This chapter is a complete, reviewable application you can run offline in CI and extend with real providers later.

## Architecture

```text
code/chapter-{n:03d}/
  {pkg}/           # domain package
  tests/           # offline unit tests
  main.py          # demo entrypoint
  Dockerfile       # container image
  pyproject.toml
  README.md
```

Core design:

1. **Ports** — LLM, storage, tools behind protocols / callables
2. **Domain service** — orchestrates turns / jobs without network I/O in tests
3. **Observability** — structured event log (JSON-friendly dicts)
4. **Packaging** — Docker + `main.py` smoke path

## Internal Implementation

```bash
cd code/chapter-{n:03d} && pytest -q && python3 main.py
```

## Production Implementation

- Swap mock LLM for real providers (OpenAI / Anthropic / gateway)
- Add auth, rate limits, persistence (Postgres / Redis)
- Wire OpenTelemetry traces and metrics exporters
- Harden with policy gates from earlier chapters

## Mini Project

Ship **{title}** as an offline-verified package with tests and Docker.

## Deployment

```bash
docker build -t ch{n:03d}-{pkg} code/chapter-{n:03d}
docker run --rm ch{n:03d}-{pkg}
```

Typical prod path: container → orchestrator (K8s / Cloud Run) → managed secrets → async workers if long-running.

## Observability

The package emits structured events (`type`, `ts` optional, payload). Export to your log stack; attach `trace_id` in production.

## Scaling Discussion

- Stateless request path scales horizontally behind a load balancer
- Session / memory state needs shared store (Redis / DB)
- Tool and LLM calls are the cost bottleneck — cache, batch, queue

## Future Improvements

- Streaming UX, multi-tenant isolation, evaluation harness, canary prompts
- Human-in-the-loop for high-risk actions
- Cost budgets and automatic model routing

## Visual diagrams

![Lifecycle](../diagrams/png/chapter-{n:03d}/lifecycle.png)

![Overview](../diagrams/png/chapter-{n:03d}/overview.png)

## Chapter Deliverables

| Artifact | Location |
|---|---|
| Manuscript | `book/chapter-{n:03d}.md` |
| Package | `code/chapter-{n:03d}/{pkg}/` |
| Tests | `code/chapter-{n:03d}/tests/` |
| Docker | `code/chapter-{n:03d}/Dockerfile` |

## Chapter Summary

{summary}

## What's Next

{next_line}
"""


def mermaid_pair(n: int, title: str, mid: str) -> None:
    d = ROOT / f"diagrams/mermaid/chapter-{n:03d}"
    write(
        d / "overview.mmd",
        f"""flowchart LR
  User[User] --> App[{title}]
  App --> Core[{mid}]
  Core --> LLM[MockLLM]
  Core --> Store[Store]
  App --> Obs[Events]
""",
    )
    write(
        d / "lifecycle.mmd",
        f"""sequenceDiagram
  participant U as User
  participant A as {title}
  participant C as Core
  participant L as MockLLM
  U->>A: request
  A->>C: handle
  C->>L: complete
  L-->>C: text
  C-->>A: result
  A-->>U: response
""",
    )


# ---------------------------------------------------------------------------
# Chapter implementations
# ---------------------------------------------------------------------------

def ch81() -> None:
    n, title, pkg = 81, "AI Chatbot", "chatbot"
    base = ROOT / f"code/chapter-{n:03d}"
    write(base / "pyproject.toml", pyproject(n))
    write(base / "README.md", readme(n, title, pkg))
    write(base / "Dockerfile", dockerfile(pkg))
    write(
        base / f"{pkg}/__init__.py",
        '''"""AI Chatbot — multi-turn session with memory and system prompt."""
from .bot import ChatMessage, ChatSession, MockLLM, ChatBot, EventLog

__all__ = ["ChatMessage", "ChatSession", "MockLLM", "ChatBot", "EventLog"]
__version__ = "1.0.0"
''',
    )
    write(
        base / f"{pkg}/bot.py",
        '''"""Multi-turn chatbot with system prompt, windowed memory, and event log."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
from collections import deque
import time
import uuid


class LLM(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> str: ...


@dataclass
class MockLLM:
    """Deterministic offline LLM."""

    prefix: str = "[bot]"

    def complete(self, messages: list[dict[str, str]]) -> str:
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return f"{self.prefix} {last_user[:200]}"


@dataclass
class ChatMessage:
    role: str
    content: str
    ts: float = field(default_factory=time.time)


@dataclass
class ChatSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: list[ChatMessage] = field(default_factory=list)
    max_turns: int = 20

    def append(self, role: str, content: str) -> ChatMessage:
        msg = ChatMessage(role=role, content=content)
        self.messages.append(msg)
        # keep last max_turns*2 messages (user+assistant pairs)
        if len(self.messages) > self.max_turns * 2 + 1:
            system = [m for m in self.messages if m.role == "system"]
            rest = [m for m in self.messages if m.role != "system"]
            self.messages = system + rest[-(self.max_turns * 2) :]
        return msg

    def as_dicts(self) -> list[dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in self.messages]


@dataclass
class EventLog:
    events: list[dict[str, Any]] = field(default_factory=list)

    def emit(self, kind: str, **payload: Any) -> None:
        self.events.append({"type": kind, "ts": time.time(), **payload})


@dataclass
class ChatBot:
    llm: LLM
    system_prompt: str = "You are a helpful assistant."
    events: EventLog = field(default_factory=EventLog)
    sessions: dict[str, ChatSession] = field(default_factory=dict)

    def new_session(self) -> ChatSession:
        s = ChatSession()
        s.append("system", self.system_prompt)
        self.sessions[s.session_id] = s
        self.events.emit("session_start", session_id=s.session_id)
        return s

    def chat(self, session_id: str, user_text: str) -> dict[str, Any]:
        if session_id not in self.sessions:
            raise KeyError(f"unknown session: {session_id}")
        s = self.sessions[session_id]
        s.append("user", user_text)
        self.events.emit("user_message", session_id=session_id, chars=len(user_text))
        reply = self.llm.complete(s.as_dicts())
        s.append("assistant", reply)
        self.events.emit("assistant_message", session_id=session_id, chars=len(reply))
        return {"session_id": session_id, "reply": reply, "turns": len([m for m in s.messages if m.role == "user"])}
''',
    )
    write(
        base / "main.py",
        '''#!/usr/bin/env python3
import json
from chatbot import ChatBot, MockLLM


def main() -> int:
    bot = ChatBot(llm=MockLLM(), system_prompt="You are Ada.")
    s = bot.new_session()
    r1 = bot.chat(s.session_id, "Hello")
    r2 = bot.chat(s.session_id, "What is 2+2?")
    print(json.dumps({"r1": r1, "r2": r2, "events": len(bot.events.events)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    )
    write(
        base / "tests/test_chatbot.py",
        '''import sys
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
''',
    )
    write(ROOT / f"book/chapter-{n:03d}.md", book_md(
        n, title, pkg,
        "AI Chatbot delivers multi-turn sessions, windowed memory, and structured events in an offline-testable package.",
        "**Chapter 82** builds PDF Chat — document-grounded Q&A.",
    ))
    mermaid_pair(n, title, "ChatSession")


def ch82() -> None:
    n, title, pkg = 82, "PDF Chat", "pdfchat"
    base = ROOT / f"code/chapter-{n:03d}"
    write(base / "pyproject.toml", pyproject(n))
    write(base / "README.md", readme(n, title, pkg))
    write(base / "Dockerfile", dockerfile(pkg))
    write(
        base / f"{pkg}/__init__.py",
        '''"""PDF Chat — chunk, index, retrieve, answer with citations."""
from .rag import Chunk, InMemoryIndex, PdfChat, MockLLM, simple_chunk

__all__ = ["Chunk", "InMemoryIndex", "PdfChat", "MockLLM", "simple_chunk"]
__version__ = "1.0.0"
''',
    )
    write(
        base / f"{pkg}/rag.py",
        '''"""Document-grounded Q&A with lexical retrieval and citation packing."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
import re
import math


def simple_chunk(text: str, *, size: int = 200, overlap: int = 40) -> list[str]:
    text = re.sub(r"\\s+", " ", text).strip()
    if not text:
        return []
    chunks: list[str] = []
    i = 0
    while i < len(text):
        chunks.append(text[i : i + size])
        i += max(1, size - overlap)
    return chunks


@dataclass
class Chunk:
    doc_id: str
    chunk_id: int
    text: str
    page: int = 1

    @property
    def citation(self) -> str:
        return f"{self.doc_id}#p{self.page}/c{self.chunk_id}"


def _tokens(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", s.lower()))


@dataclass
class InMemoryIndex:
    chunks: list[Chunk] = field(default_factory=list)

    def add(self, doc_id: str, text: str, *, page: int = 1) -> int:
        parts = simple_chunk(text)
        for i, p in enumerate(parts):
            self.chunks.append(Chunk(doc_id=doc_id, chunk_id=i, text=p, page=page))
        return len(parts)

    def search(self, query: str, *, k: int = 3) -> list[tuple[float, Chunk]]:
        q = _tokens(query)
        if not q:
            return []
        scored: list[tuple[float, Chunk]] = []
        for c in self.chunks:
            t = _tokens(c.text)
            if not t:
                continue
            inter = len(q & t)
            union = len(q | t)
            score = inter / union if union else 0.0
            # prefer denser matches
            score += 0.01 * inter
            if score > 0:
                scored.append((score, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:k]


class LLM(Protocol):
    def complete(self, prompt: str) -> str: ...


@dataclass
class MockLLM:
    def complete(self, prompt: str) -> str:
        # echo a short grounded answer marker
        return f"[grounded] {prompt[-120:]}"


@dataclass
class PdfChat:
    index: InMemoryIndex
    llm: LLM
    events: list[dict[str, Any]] = field(default_factory=list)

    def ingest(self, doc_id: str, text: str, *, page: int = 1) -> dict[str, Any]:
        n = self.index.add(doc_id, text, page=page)
        ev = {"type": "ingest", "doc_id": doc_id, "chunks": n}
        self.events.append(ev)
        return ev

    def ask(self, question: str, *, k: int = 3) -> dict[str, Any]:
        hits = self.index.search(question, k=k)
        context = "\\n---\\n".join(f"[{c.citation}] {c.text}" for _, c in hits)
        prompt = f"Context:\\n{context}\\n\\nQuestion: {question}\\nAnswer with citations."
        answer = self.llm.complete(prompt)
        citations = [c.citation for _, c in hits]
        out = {
            "answer": answer,
            "citations": citations,
            "scores": [round(s, 4) for s, _ in hits],
        }
        self.events.append({"type": "ask", "q": question, "n_hits": len(hits)})
        return out
''',
    )
    write(
        base / "main.py",
        '''#!/usr/bin/env python3
import json
from pdfchat import PdfChat, InMemoryIndex, MockLLM


def main() -> int:
    app = PdfChat(index=InMemoryIndex(), llm=MockLLM())
    app.ingest("handbook", "Agent memory stores conversation state. Vector indexes speed retrieval.")
    app.ingest("handbook", "Evaluation uses golden datasets and scorers for quality gates.", page=2)
    r = app.ask("How does agent memory work?")
    print(json.dumps(r, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    )
    write(
        base / "tests/test_pdfchat.py",
        '''import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pdfchat import PdfChat, InMemoryIndex, MockLLM, simple_chunk


def test_chunk():
    parts = simple_chunk("a " * 100, size=20, overlap=5)
    assert len(parts) >= 2


def test_retrieve_and_cite():
    app = PdfChat(index=InMemoryIndex(), llm=MockLLM())
    app.ingest("docA", "The capital of France is Paris. Paris is a city.")
    app.ingest("docB", "Python is a programming language used for agents.")
    r = app.ask("capital of France Paris")
    assert r["citations"]
    assert any("docA" in c for c in r["citations"])
    assert r["answer"].startswith("[grounded]")
''',
    )
    write(ROOT / f"book/chapter-{n:03d}.md", book_md(
        n, title, pkg,
        "PDF Chat chunks documents, retrieves by lexical overlap, and answers with citations.",
        "**Chapter 83** builds a Research Agent that plans, searches, and synthesizes.",
    ))
    mermaid_pair(n, title, "RAG")


def ch83() -> None:
    n, title, pkg = 83, "Research Agent", "research"
    base = ROOT / f"code/chapter-{n:03d}"
    write(base / "pyproject.toml", pyproject(n))
    write(base / "README.md", readme(n, title, pkg))
    write(base / "Dockerfile", dockerfile(pkg))
    write(
        base / f"{pkg}/__init__.py",
        '''"""Research Agent — plan, search, read, synthesize."""
from .agent import ResearchAgent, MockSearch, MockLLM, ResearchReport

__all__ = ["ResearchAgent", "MockSearch", "MockLLM", "ResearchReport"]
__version__ = "1.0.0"
''',
    )
    write(
        base / f"{pkg}/agent.py",
        '''"""Plan → search → extract → synthesize research loop."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class SearchBackend(Protocol):
    def search(self, query: str, *, k: int = 5) -> list[dict[str, str]]: ...


class LLM(Protocol):
    def complete(self, prompt: str) -> str: ...


@dataclass
class MockSearch:
    corpus: list[dict[str, str]] = field(default_factory=list)

    def search(self, query: str, *, k: int = 5) -> list[dict[str, str]]:
        q = query.lower().split()
        scored = []
        for doc in self.corpus:
            blob = (doc.get("title", "") + " " + doc.get("snippet", "")).lower()
            score = sum(1 for t in q if t in blob)
            if score:
                scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for _, d in scored[:k]]


@dataclass
class MockLLM:
    def complete(self, prompt: str) -> str:
        if prompt.startswith("PLAN:"):
            topic = prompt.split(":", 1)[1].strip()
            return "\\n".join([f"What is {topic}?", f"{topic} benefits", f"{topic} risks"])
        if prompt.startswith("SYNTH:"):
            return f"Summary based on sources:\\n{prompt[6:400]}"
        return prompt[:200]


@dataclass
class ResearchReport:
    topic: str
    subquestions: list[str]
    sources: list[dict[str, str]]
    synthesis: str
    events: list[dict[str, Any]]


@dataclass
class ResearchAgent:
    search: SearchBackend
    llm: LLM
    max_subqs: int = 3

    def run(self, topic: str) -> ResearchReport:
        events: list[dict[str, Any]] = [{"type": "start", "topic": topic}]
        plan_raw = self.llm.complete(f"PLAN:{topic}")
        subqs = [ln.strip() for ln in plan_raw.splitlines() if ln.strip()][: self.max_subqs]
        events.append({"type": "plan", "subqs": subqs})
        sources: list[dict[str, str]] = []
        seen: set[str] = set()
        for sq in subqs:
            hits = self.search.search(sq, k=3)
            events.append({"type": "search", "q": sq, "hits": len(hits)})
            for h in hits:
                key = h.get("url") or h.get("title") or str(h)
                if key not in seen:
                    seen.add(key)
                    sources.append(h)
        packed = "\\n".join(f"- {s.get('title', '?')}: {s.get('snippet', '')[:120]}" for s in sources)
        synthesis = self.llm.complete(f"SYNTH:{packed}")
        events.append({"type": "done", "n_sources": len(sources)})
        return ResearchReport(
            topic=topic,
            subquestions=subqs,
            sources=sources,
            synthesis=synthesis,
            events=events,
        )
''',
    )
    write(
        base / "main.py",
        '''#!/usr/bin/env python3
import json
from research import ResearchAgent, MockSearch, MockLLM


def main() -> int:
    search = MockSearch(
        corpus=[
            {"title": "Agents 101", "url": "u1", "snippet": "AI agents plan and use tools."},
            {"title": "Risks", "url": "u2", "snippet": "Agent risks include runaway actions."},
            {"title": "Benefits", "url": "u3", "snippet": "Agents automate research workflows."},
        ]
    )
    agent = ResearchAgent(search=search, llm=MockLLM())
    report = agent.run("AI agents")
    print(json.dumps({
        "topic": report.topic,
        "subqs": report.subquestions,
        "sources": len(report.sources),
        "synthesis": report.synthesis[:200],
        "events": len(report.events),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    )
    write(
        base / "tests/test_research.py",
        '''import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research import ResearchAgent, MockSearch, MockLLM


def test_research_loop():
    search = MockSearch(corpus=[
        {"title": "A", "url": "1", "snippet": "vector databases store embeddings"},
        {"title": "B", "url": "2", "snippet": "risks of vector databases"},
    ])
    agent = ResearchAgent(search=search, llm=MockLLM())
    r = agent.run("vector databases")
    assert r.subquestions
    assert r.synthesis
    assert any(e["type"] == "done" for e in r.events)
''',
    )
    write(ROOT / f"book/chapter-{n:03d}.md", book_md(
        n, title, pkg,
        "Research Agent plans sub-questions, searches a corpus, and synthesizes a cited summary.",
        "**Chapter 84** builds a Browser Agent with a sandboxed tool loop.",
    ))
    mermaid_pair(n, title, "PlanSearchSynth")


def ch84() -> None:
    n, title, pkg = 84, "Browser Agent", "browser"
    base = ROOT / f"code/chapter-{n:03d}"
    write(base / "pyproject.toml", pyproject(n))
    write(base / "README.md", readme(n, title, pkg))
    write(base / "Dockerfile", dockerfile(pkg))
    write(
        base / f"{pkg}/__init__.py",
        '''"""Browser Agent — navigate, extract, act via tool interface (mocked DOM)."""
from .agent import BrowserAgent, MockBrowser, MockLLM, Page

__all__ = ["BrowserAgent", "MockBrowser", "MockLLM", "Page"]
__version__ = "1.0.0"
''',
    )
    write(
        base / f"{pkg}/agent.py",
        '''"""Browser automation agent over a mock page graph (no real network)."""
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
        if "pricing" in g and ("/pricing" in obs or "$" in observation or ("plan" in obs and "pro" in obs)):
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
''',
    )
    write(
        base / "main.py",
        '''#!/usr/bin/env python3
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
''',
    )
    write(
        base / "tests/test_browser.py",
        '''import sys
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
''',
    )
    write(ROOT / f"book/chapter-{n:03d}.md", book_md(
        n, title, pkg,
        "Browser Agent drives a mocked page graph with plan-act-observe steps and offline tests.",
        "**Chapter 85** builds a SQL Agent with guarded query generation.",
    ))
    mermaid_pair(n, title, "BrowseLoop")


def ch85() -> None:
    n, title, pkg = 85, "SQL Agent", "sqlagent"
    base = ROOT / f"code/chapter-{n:03d}"
    write(base / "pyproject.toml", pyproject(n))
    write(base / "README.md", readme(n, title, pkg))
    write(base / "Dockerfile", dockerfile(pkg))
    write(
        base / f"{pkg}/__init__.py",
        '''"""SQL Agent — NL→SQL with schema, allowlist, and dry-run safety."""
from .agent import SQLAgent, MockDB, MockLLM, Schema, FORBIDDEN

__all__ = ["SQLAgent", "MockDB", "MockLLM", "Schema", "FORBIDDEN"]
__version__ = "1.0.0"
''',
    )
    write(
        base / f"{pkg}/agent.py",
        '''"""Natural-language to SQL with read-only guards."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
import re


FORBIDDEN = re.compile(
    r"\\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|ATTACH|DETACH)\\b",
    re.I,
)


@dataclass
class Schema:
    tables: dict[str, list[str]]  # table -> columns

    def ddl_summary(self) -> str:
        lines = []
        for t, cols in self.tables.items():
            lines.append(f"TABLE {t}({', '.join(cols)})")
        return "\\n".join(lines)


@dataclass
class MockDB:
    schema: Schema
    data: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    def execute_readonly(self, sql: str) -> list[dict[str, Any]]:
        if FORBIDDEN.search(sql):
            raise PermissionError("write/DDL not allowed")
        # tiny SELECT parser: SELECT cols FROM table [WHERE col = val]
        m = re.match(
            r"SELECT\\s+(.+?)\\s+FROM\\s+(\\w+)(?:\\s+WHERE\\s+(\\w+)\\s*=\\s*'([^']*)')?\\s*;?\\s*$",
            sql.strip(),
            re.I | re.S,
        )
        if not m:
            raise ValueError(f"unsupported SQL: {sql}")
        cols_raw, table, where_col, where_val = m.group(1), m.group(2), m.group(3), m.group(4)
        if table not in self.schema.tables:
            raise KeyError(f"unknown table: {table}")
        rows = list(self.data.get(table, []))
        if where_col:
            rows = [r for r in rows if str(r.get(where_col)) == where_val]
        if cols_raw.strip() == "*":
            return rows
        cols = [c.strip() for c in cols_raw.split(",")]
        return [{c: r.get(c) for c in cols} for r in rows]


class LLM(Protocol):
    def nl_to_sql(self, question: str, schema: str) -> str: ...


@dataclass
class MockLLM:
    def nl_to_sql(self, question: str, schema: str) -> str:
        q = question.lower()
        if "users" in q and "alice" in q:
            return "SELECT * FROM users WHERE name = 'alice';"
        if "count" in q and "orders" in q:
            # mock engine doesn't aggregate — return all for demo
            return "SELECT * FROM orders;"
        if "orders" in q:
            return "SELECT * FROM orders;"
        if "users" in q:
            return "SELECT * FROM users;"
        return "SELECT * FROM users;"


@dataclass
class SQLAgent:
    db: MockDB
    llm: LLM
    events: list[dict[str, Any]] = field(default_factory=list)

    def ask(self, question: str) -> dict[str, Any]:
        schema = self.db.schema.ddl_summary()
        sql = self.llm.nl_to_sql(question, schema).strip()
        self.events.append({"type": "sql_generated", "sql": sql})
        if FORBIDDEN.search(sql):
            self.events.append({"type": "blocked", "sql": sql})
            raise PermissionError(f"blocked SQL: {sql}")
        # only allow known tables
        tables = set(self.db.schema.tables)
        for t in re.findall(r"\\bFROM\\s+(\\w+)", sql, flags=re.I):
            if t not in tables:
                raise PermissionError(f"table not allowlisted: {t}")
        rows = self.db.execute_readonly(sql)
        self.events.append({"type": "executed", "n": len(rows)})
        return {"sql": sql, "rows": rows, "n": len(rows)}
''',
    )
    write(
        base / "main.py",
        '''#!/usr/bin/env python3
import json
from sqlagent import SQLAgent, MockDB, MockLLM, Schema


def main() -> int:
    schema = Schema(tables={"users": ["id", "name"], "orders": ["id", "user_id", "total"]})
    db = MockDB(
        schema=schema,
        data={
            "users": [{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}],
            "orders": [{"id": 10, "user_id": 1, "total": 50}],
        },
    )
    agent = SQLAgent(db=db, llm=MockLLM())
    print(json.dumps(agent.ask("show users named alice"), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    )
    write(
        base / "tests/test_sqlagent.py",
        '''import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlagent import SQLAgent, MockDB, MockLLM, Schema, FORBIDDEN


def _agent():
    schema = Schema(tables={"users": ["id", "name"], "orders": ["id", "user_id", "total"]})
    db = MockDB(
        schema=schema,
        data={
            "users": [{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}],
            "orders": [{"id": 10, "user_id": 1, "total": 50}],
        },
    )
    return SQLAgent(db=db, llm=MockLLM())


def test_select_user():
    r = _agent().ask("users named alice")
    assert r["n"] == 1
    assert r["rows"][0]["name"] == "alice"


def test_block_write():
    agent = _agent()
    with pytest.raises(PermissionError):
        agent.db.execute_readonly("DELETE FROM users;")


def test_forbidden_regex():
    assert FORBIDDEN.search("DROP TABLE users")
''',
    )
    write(ROOT / f"book/chapter-{n:03d}.md", book_md(
        n, title, pkg,
        "SQL Agent maps NL to read-only SQL with schema allowlists and write/DDL blocking.",
        "**Chapter 86** builds an Email Agent for triage and draft replies.",
    ))
    mermaid_pair(n, title, "NL2SQL")


def ch86() -> None:
    n, title, pkg = 86, "Email Agent", "emailagent"
    base = ROOT / f"code/chapter-{n:03d}"
    write(base / "pyproject.toml", pyproject(n))
    write(base / "README.md", readme(n, title, pkg))
    write(base / "Dockerfile", dockerfile(pkg))
    write(
        base / f"{pkg}/__init__.py",
        '''"""Email Agent — classify, prioritize, draft replies (no real SMTP)."""
from .agent import Email, EmailAgent, MockLLM, MockMailbox

__all__ = ["Email", "EmailAgent", "MockLLM", "MockMailbox"]
__version__ = "1.0.0"
''',
    )
    write(
        base / f"{pkg}/agent.py",
        '''"""Inbox triage and draft generation with policy tags."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
import re


@dataclass
class Email:
    id: str
    sender: str
    subject: str
    body: str
    labels: list[str] = field(default_factory=list)


@dataclass
class MockMailbox:
    inbox: list[Email] = field(default_factory=list)
    outbox: list[dict[str, str]] = field(default_factory=list)

    def list_inbox(self) -> list[Email]:
        return list(self.inbox)

    def send(self, *, to: str, subject: str, body: str) -> dict[str, str]:
        msg = {"to": to, "subject": subject, "body": body}
        self.outbox.append(msg)
        return msg


class LLM(Protocol):
    def classify(self, email: Email) -> dict[str, Any]: ...
    def draft(self, email: Email, policy: str) -> str: ...


@dataclass
class MockLLM:
    def classify(self, email: Email) -> dict[str, Any]:
        text = f"{email.subject} {email.body}".lower()
        priority = "high" if any(w in text for w in ("urgent", "asap", "outage", "down")) else "normal"
        if any(w in text for w in ("invoice", "payment", "bill")):
            category = "billing"
        elif any(w in text for w in ("bug", "error", "broken")):
            category = "support"
        elif any(w in text for w in ("hello", "intro", "meet")):
            category = "intro"
        else:
            category = "general"
        spam = bool(re.search(r"\\b(viagra|lottery|prince)\\b", text))
        return {"priority": "low" if spam else priority, "category": "spam" if spam else category, "spam": spam}

    def draft(self, email: Email, policy: str) -> str:
        return f"Hi,\\n\\nThanks for your note about '{email.subject}'. {policy}\\n\\nBest regards"


@dataclass
class EmailAgent:
    mailbox: MockMailbox
    llm: LLM
    reply_policy: str = "We will follow up within one business day."
    events: list[dict[str, Any]] = field(default_factory=list)
    auto_send: bool = False

    def triage(self) -> list[dict[str, Any]]:
        results = []
        for em in self.mailbox.list_inbox():
            meta = self.llm.classify(em)
            em.labels = [meta["category"], meta["priority"]]
            row = {"id": em.id, **meta, "subject": em.subject}
            results.append(row)
            self.events.append({"type": "classify", **row})
        results.sort(key=lambda r: 0 if r["priority"] == "high" else 1)
        return results

    def draft_reply(self, email_id: str) -> dict[str, Any]:
        em = next((e for e in self.mailbox.inbox if e.id == email_id), None)
        if not em:
            raise KeyError(email_id)
        meta = self.llm.classify(em)
        if meta.get("spam"):
            self.events.append({"type": "skip_spam", "id": email_id})
            return {"id": email_id, "skipped": True, "reason": "spam"}
        body = self.llm.draft(em, self.reply_policy)
        draft = {"id": email_id, "to": em.sender, "subject": f"Re: {em.subject}", "body": body}
        self.events.append({"type": "draft", "id": email_id})
        if self.auto_send:
            self.mailbox.send(to=draft["to"], subject=draft["subject"], body=draft["body"])
            self.events.append({"type": "sent", "id": email_id})
            draft["sent"] = True
        else:
            draft["sent"] = False
        return draft
''',
    )
    write(
        base / "main.py",
        '''#!/usr/bin/env python3
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
''',
    )
    write(
        base / "tests/test_emailagent.py",
        '''import sys
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
''',
    )
    write(ROOT / f"book/chapter-{n:03d}.md", book_md(
        n, title, pkg,
        "Email Agent triages inbox by priority/category, skips spam, and drafts policy-aware replies.",
        "**Chapter 87** builds a Meeting Assistant for notes and action items.",
    ))
    mermaid_pair(n, title, "TriageDraft")


def ch87() -> None:
    n, title, pkg = 87, "Meeting Assistant", "meeting"
    base = ROOT / f"code/chapter-{n:03d}"
    write(base / "pyproject.toml", pyproject(n))
    write(base / "README.md", readme(n, title, pkg))
    write(base / "Dockerfile", dockerfile(pkg))
    write(
        base / f"{pkg}/__init__.py",
        '''"""Meeting Assistant — transcript → summary, decisions, action items."""
from .assistant import MeetingAssistant, Transcript, MockLLM, ActionItem

__all__ = ["MeetingAssistant", "Transcript", "MockLLM", "ActionItem"]
__version__ = "1.0.0"
''',
    )
    write(
        base / f"{pkg}/assistant.py",
        '''"""Meeting notes pipeline over a transcript."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
import re


@dataclass
class ActionItem:
    owner: str
    task: str
    due: str | None = None


@dataclass
class Transcript:
    meeting_id: str
    title: str
    lines: list[str]  # "Speaker: text"

    @property
    def text(self) -> str:
        return "\\n".join(self.lines)


class LLM(Protocol):
    def summarize(self, text: str) -> str: ...
    def extract_actions(self, text: str) -> list[ActionItem]: ...
    def extract_decisions(self, text: str) -> list[str]: ...


@dataclass
class MockLLM:
    def summarize(self, text: str) -> str:
        speakers = sorted({ln.split(":", 1)[0] for ln in text.splitlines() if ":" in ln})
        return f"Meeting with {', '.join(speakers)}. Key discussion captured ({len(text)} chars)."

    def extract_actions(self, text: str) -> list[ActionItem]:
        items: list[ActionItem] = []
        for ln in text.splitlines():
            m = re.search(r"(?i)(\\w+)\\s+will\\s+(.+?)(?:\\s+by\\s+(\\w+))?$", ln.strip())
            if m:
                items.append(ActionItem(owner=m.group(1), task=m.group(2).strip(" ."), due=m.group(3)))
            m2 = re.search(r"(?i)ACTION[:\\s]+(\\w+):\\s*(.+)", ln)
            if m2:
                items.append(ActionItem(owner=m2.group(1), task=m2.group(2).strip()))
        return items

    def extract_decisions(self, text: str) -> list[str]:
        out = []
        for ln in text.splitlines():
            if re.search(r"(?i)\\b(decided|decision|agreed)\\b", ln):
                out.append(ln.strip())
        return out


@dataclass
class MeetingAssistant:
    llm: LLM
    events: list[dict[str, Any]] = field(default_factory=list)

    def process(self, transcript: Transcript) -> dict[str, Any]:
        self.events.append({"type": "process_start", "meeting_id": transcript.meeting_id})
        summary = self.llm.summarize(transcript.text)
        actions = self.llm.extract_actions(transcript.text)
        decisions = self.llm.extract_decisions(transcript.text)
        report = {
            "meeting_id": transcript.meeting_id,
            "title": transcript.title,
            "summary": summary,
            "decisions": decisions,
            "action_items": [
                {"owner": a.owner, "task": a.task, "due": a.due} for a in actions
            ],
        }
        self.events.append({"type": "process_done", "n_actions": len(actions)})
        return report
''',
    )
    write(
        base / "main.py",
        '''#!/usr/bin/env python3
import json
from meeting import MeetingAssistant, Transcript, MockLLM


def main() -> int:
    t = Transcript(
        meeting_id="m1",
        title="Sprint planning",
        lines=[
            "Ada: We need to ship the API.",
            "Bob: Decided we will use FastAPI.",
            "Ada: Bob will write the OpenAPI spec by Friday.",
            "ACTION: Ada: review PR #12",
        ],
    )
    report = MeetingAssistant(llm=MockLLM()).process(t)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    )
    write(
        base / "tests/test_meeting.py",
        '''import sys
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
''',
    )
    write(ROOT / f"book/chapter-{n:03d}.md", book_md(
        n, title, pkg,
        "Meeting Assistant turns transcripts into summaries, decisions, and action items.",
        "**Chapter 88** builds a Customer Support Agent with knowledge + tickets.",
    ))
    mermaid_pair(n, title, "NotesPipeline")


def ch88() -> None:
    n, title, pkg = 88, "Customer Support Agent", "support"
    base = ROOT / f"code/chapter-{n:03d}"
    write(base / "pyproject.toml", pyproject(n))
    write(base / "README.md", readme(n, title, pkg))
    write(base / "Dockerfile", dockerfile(pkg))
    write(
        base / f"{pkg}/__init__.py",
        '''"""Customer Support Agent — KB retrieval, reply, escalate, ticket state."""
from .agent import SupportAgent, Ticket, KnowledgeBase, MockLLM

__all__ = ["SupportAgent", "Ticket", "KnowledgeBase", "MockLLM"]
__version__ = "1.0.0"
''',
    )
    write(
        base / f"{pkg}/agent.py",
        '''"""Tier-1 support agent with KB grounding and escalation rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
import re
import time
import uuid


@dataclass
class Ticket:
    id: str
    user: str
    message: str
    status: str = "open"  # open|resolved|escalated
    priority: str = "normal"
    history: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class KnowledgeBase:
    articles: list[dict[str, str]] = field(default_factory=list)

    def search(self, query: str, *, k: int = 2) -> list[dict[str, str]]:
        q = set(re.findall(r"[a-z0-9]+", query.lower()))
        scored = []
        for a in self.articles:
            blob = set(re.findall(r"[a-z0-9]+", (a["title"] + " " + a["body"]).lower()))
            score = len(q & blob)
            if score:
                scored.append((score, a))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [a for _, a in scored[:k]]


class LLM(Protocol):
    def reply(self, message: str, articles: list[dict[str, str]]) -> str: ...
    def needs_escalation(self, message: str) -> bool: ...


@dataclass
class MockLLM:
    def reply(self, message: str, articles: list[dict[str, str]]) -> str:
        if not articles:
            return "I could not find a KB article. Escalating to a human agent."
        titles = ", ".join(a["title"] for a in articles)
        return f"Based on {titles}: {articles[0]['body'][:160]}"

    def needs_escalation(self, message: str) -> bool:
        m = message.lower()
        return any(w in m for w in ("lawyer", "lawsuit", "chargeback", "speak to manager", "human"))


@dataclass
class SupportAgent:
    kb: KnowledgeBase
    llm: LLM
    tickets: dict[str, Ticket] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    def open_ticket(self, user: str, message: str) -> Ticket:
        t = Ticket(id=str(uuid.uuid4())[:8], user=user, message=message)
        if any(w in message.lower() for w in ("urgent", "down", "outage")):
            t.priority = "high"
        self.tickets[t.id] = t
        self.events.append({"type": "ticket_open", "id": t.id, "priority": t.priority})
        return t

    def handle(self, ticket_id: str) -> dict[str, Any]:
        t = self.tickets[ticket_id]
        if self.llm.needs_escalation(t.message):
            t.status = "escalated"
            t.history.append({"ts": time.time(), "event": "escalated"})
            self.events.append({"type": "escalated", "id": t.id})
            return {"ticket_id": t.id, "status": t.status, "reply": None, "escalated": True}
        articles = self.kb.search(t.message)
        reply = self.llm.reply(t.message, articles)
        t.history.append({"ts": time.time(), "event": "reply", "n_articles": len(articles)})
        if articles:
            t.status = "resolved"
        else:
            t.status = "escalated"
        self.events.append({"type": "handled", "id": t.id, "status": t.status})
        return {
            "ticket_id": t.id,
            "status": t.status,
            "reply": reply,
            "articles": [a["id"] for a in articles],
            "escalated": t.status == "escalated",
        }
''',
    )
    write(
        base / "main.py",
        '''#!/usr/bin/env python3
import json
from support import SupportAgent, KnowledgeBase, MockLLM


def main() -> int:
    kb = KnowledgeBase(articles=[
        {"id": "kb1", "title": "Reset password", "body": "Use Settings > Security > Reset password link."},
        {"id": "kb2", "title": "API downtime", "body": "Check status page; incidents resolve within 1 hour SLA."},
    ])
    agent = SupportAgent(kb=kb, llm=MockLLM())
    t1 = agent.open_ticket("u1", "How do I reset password?")
    t2 = agent.open_ticket("u2", "I want to speak to manager about chargeback")
    print(json.dumps({"a": agent.handle(t1.id), "b": agent.handle(t2.id)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    )
    write(
        base / "tests/test_support.py",
        '''import sys
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
''',
    )
    write(ROOT / f"book/chapter-{n:03d}.md", book_md(
        n, title, pkg,
        "Customer Support Agent opens tickets, retrieves KB articles, replies, and escalates policy cases.",
        "**Chapter 89** builds a Coding Agent with edit/test loops.",
    ))
    mermaid_pair(n, title, "TicketKB")


def ch89() -> None:
    n, title, pkg = 89, "Coding Agent", "coding"
    base = ROOT / f"code/chapter-{n:03d}"
    write(base / "pyproject.toml", pyproject(n))
    write(base / "README.md", readme(n, title, pkg))
    write(base / "Dockerfile", dockerfile(pkg))
    write(
        base / f"{pkg}/__init__.py",
        '''"""Coding Agent — propose edits, run tests in a workspace sandbox."""
from .agent import CodingAgent, Workspace, MockLLM, TestRunner

__all__ = ["CodingAgent", "Workspace", "MockLLM", "TestRunner"]
__version__ = "1.0.0"
''',
    )
    write(
        base / f"{pkg}/agent.py",
        '''"""Lightweight coding agent over an in-memory workspace."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
import re


@dataclass
class Workspace:
    files: dict[str, str] = field(default_factory=dict)

    def read(self, path: str) -> str:
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]

    def write(self, path: str, content: str) -> None:
        self.files[path] = content

    def list_files(self) -> list[str]:
        return sorted(self.files)


@dataclass
class TestRunner:
    """Runs simple assertion snippets embedded in tests.py style content."""

    def run(self, ws: Workspace, test_path: str = "tests.py") -> dict[str, Any]:
        if test_path not in ws.files:
            return {"ok": False, "error": "no tests"}
        # Execute tests in restricted namespace with workspace files loaded as modules-like dict
        ns: dict[str, Any] = {"__name__": "tests"}
        # expose other files as simple string constants for demos
        for p, c in ws.files.items():
            if p.endswith(".py") and p != test_path:
                try:
                    exec(compile(c, p, "exec"), ns)  # noqa: S102 — intentional sandbox demo
                except Exception as e:  # noqa: BLE001
                    return {"ok": False, "error": f"import {p}: {e}"}
        try:
            exec(compile(ws.files[test_path], test_path, "exec"), ns)  # noqa: S102
        except AssertionError as e:
            return {"ok": False, "error": f"assert: {e}"}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": str(e)}
        return {"ok": True, "error": None}


class LLM(Protocol):
    def plan(self, goal: str, files: list[str]) -> list[dict[str, str]]: ...


@dataclass
class MockLLM:
    def plan(self, goal: str, files: list[str]) -> list[dict[str, str]]:
        g = goal.lower()
        if "add" in g and "add" in g and "function" in g:
            # add add(a,b) to mathutil.py
            return [
                {
                    "action": "write",
                    "path": "mathutil.py",
                    "content": "def add(a, b):\\n    return a + b\\n",
                },
                {
                    "action": "write",
                    "path": "tests.py",
                    "content": "assert add(2, 3) == 5\\nassert add(0, 0) == 0\\n",
                },
            ]
        if "fix" in g and "multiply" in g:
            return [
                {
                    "action": "write",
                    "path": "mathutil.py",
                    "content": "def multiply(a, b):\\n    return a * b\\n",
                },
                {
                    "action": "write",
                    "path": "tests.py",
                    "content": "assert multiply(3, 4) == 12\\n",
                },
            ]
        return [{"action": "noop", "path": "", "content": ""}]


@dataclass
class CodingAgent:
    workspace: Workspace
    llm: LLM
    runner: TestRunner = field(default_factory=TestRunner)
    max_iters: int = 3
    events: list[dict[str, Any]] = field(default_factory=list)

    def run(self, goal: str) -> dict[str, Any]:
        self.events.append({"type": "start", "goal": goal})
        last_test: dict[str, Any] = {"ok": False, "error": "not run"}
        for i in range(self.max_iters):
            steps = self.llm.plan(goal, self.workspace.list_files())
            self.events.append({"type": "plan", "iter": i, "steps": len(steps)})
            for step in steps:
                if step.get("action") == "write" and step.get("path"):
                    self.workspace.write(step["path"], step["content"])
                    self.events.append({"type": "write", "path": step["path"]})
            last_test = self.runner.run(self.workspace)
            self.events.append({"type": "test", "iter": i, **last_test})
            if last_test.get("ok"):
                break
        return {
            "goal": goal,
            "ok": bool(last_test.get("ok")),
            "files": self.workspace.list_files(),
            "test": last_test,
            "events": self.events,
        }
''',
    )
    write(
        base / "main.py",
        '''#!/usr/bin/env python3
import json
from coding import CodingAgent, Workspace, MockLLM


def main() -> int:
    agent = CodingAgent(workspace=Workspace(), llm=MockLLM())
    out = agent.run("add function add(a,b)")
    print(json.dumps({"ok": out["ok"], "files": out["files"], "test": out["test"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    )
    write(
        base / "tests/test_coding.py",
        '''import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coding import CodingAgent, Workspace, MockLLM


def test_add_function_passes():
    agent = CodingAgent(workspace=Workspace(), llm=MockLLM())
    out = agent.run("add function add")
    assert out["ok"] is True
    assert "mathutil.py" in out["files"]


def test_multiply():
    agent = CodingAgent(workspace=Workspace(), llm=MockLLM())
    out = agent.run("fix multiply")
    assert out["ok"] is True
''',
    )
    write(ROOT / f"book/chapter-{n:03d}.md", book_md(
        n, title, pkg,
        "Coding Agent plans file writes in a sandbox workspace and iterates until tests pass.",
        "**Chapter 90** assembles a Multi-Agent Platform coordinating specialists.",
    ))
    mermaid_pair(n, title, "EditTestLoop")


def ch90() -> None:
    n, title, pkg = 90, "Multi-Agent Platform", "multiagent"
    base = ROOT / f"code/chapter-{n:03d}"
    write(base / "pyproject.toml", pyproject(n))
    write(base / "README.md", readme(n, title, pkg))
    write(base / "Dockerfile", dockerfile(pkg))
    write(
        base / f"{pkg}/__init__.py",
        '''"""Multi-Agent Platform — router, specialists, shared bus, final merge."""
from .platform import AgentSpec, MessageBus, Router, MultiAgentPlatform, MockLLM

__all__ = ["AgentSpec", "MessageBus", "Router", "MultiAgentPlatform", "MockLLM"]
__version__ = "1.0.0"
''',
    )
    write(
        base / f"{pkg}/platform.py",
        '''"""Composable multi-agent orchestration platform."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol
import time
import uuid


@dataclass
class AgentMessage:
    id: str
    sender: str
    recipient: str
    content: str
    kind: str = "task"  # task|result|broadcast
    meta: dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)


@dataclass
class MessageBus:
    log: list[AgentMessage] = field(default_factory=list)

    def send(self, msg: AgentMessage) -> None:
        self.log.append(msg)

    def for_recipient(self, name: str) -> list[AgentMessage]:
        return [m for m in self.log if m.recipient == name or m.recipient == "*"]


Handler = Callable[[str, dict[str, Any]], str]


@dataclass
class AgentSpec:
    name: str
    skills: list[str]
    handler: Handler


@dataclass
class Router:
    agents: list[AgentSpec]

    def route(self, task: str) -> AgentSpec:
        t = task.lower()
        best: AgentSpec | None = None
        best_score = -1
        for a in self.agents:
            score = sum(1 for s in a.skills if s.lower() in t)
            if score > best_score:
                best_score = score
                best = a
        if best is None:
            raise RuntimeError("no agents")
        # default first agent if no skill match
        if best_score <= 0:
            return self.agents[0]
        return best


class LLM(Protocol):
    def merge(self, task: str, parts: list[str]) -> str: ...


@dataclass
class MockLLM:
    def merge(self, task: str, parts: list[str]) -> str:
        body = " | ".join(parts)
        return f"Merged for '{task}': {body}"


@dataclass
class MultiAgentPlatform:
    agents: list[AgentSpec]
    llm: LLM
    bus: MessageBus = field(default_factory=MessageBus)
    events: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.router = Router(self.agents)

    def run(self, task: str, *, fanout: bool = False) -> dict[str, Any]:
        run_id = str(uuid.uuid4())[:8]
        self.events.append({"type": "run_start", "run_id": run_id, "task": task})
        if fanout:
            selected = list(self.agents)
        else:
            selected = [self.router.route(task)]
        results: list[str] = []
        for agent in selected:
            msg = AgentMessage(
                id=str(uuid.uuid4())[:8],
                sender="orchestrator",
                recipient=agent.name,
                content=task,
            )
            self.bus.send(msg)
            out = agent.handler(task, {"run_id": run_id})
            self.bus.send(
                AgentMessage(
                    id=str(uuid.uuid4())[:8],
                    sender=agent.name,
                    recipient="orchestrator",
                    content=out,
                    kind="result",
                )
            )
            results.append(f"{agent.name}: {out}")
            self.events.append({"type": "agent_result", "agent": agent.name})
        final = self.llm.merge(task, results) if len(results) > 1 else results[0]
        self.events.append({"type": "run_done", "run_id": run_id})
        return {
            "run_id": run_id,
            "task": task,
            "agents": [a.name for a in selected],
            "result": final,
            "bus_size": len(self.bus.log),
            "events": self.events,
        }
''',
    )
    write(
        base / "main.py",
        '''#!/usr/bin/env python3
import json
from multiagent import AgentSpec, MultiAgentPlatform, MockLLM


def main() -> int:
    agents = [
        AgentSpec("researcher", ["research", "search"], lambda t, _: f"notes on {t}"),
        AgentSpec("coder", ["code", "implement", "fix"], lambda t, _: f"patch for {t}"),
        AgentSpec("writer", ["write", "summary", "blog"], lambda t, _: f"draft for {t}"),
    ]
    plat = MultiAgentPlatform(agents=agents, llm=MockLLM())
    one = plat.run("implement fix for login")
    many = MultiAgentPlatform(agents=agents, llm=MockLLM()).run("research and write summary", fanout=True)
    print(json.dumps({"single": {"agents": one["agents"], "result": one["result"]},
                      "fanout": {"agents": many["agents"], "result": many["result"]}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    )
    write(
        base / "tests/test_multiagent.py",
        '''import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from multiagent import AgentSpec, MultiAgentPlatform, MockLLM, Router


def _agents():
    return [
        AgentSpec("researcher", ["research", "search"], lambda t, _: f"notes on {t}"),
        AgentSpec("coder", ["code", "implement", "fix"], lambda t, _: f"patch for {t}"),
        AgentSpec("writer", ["write", "summary"], lambda t, _: f"draft for {t}"),
    ]


def test_route_coder():
    r = Router(_agents())
    assert r.route("implement feature") .name == "coder"


def test_single_and_fanout():
    plat = MultiAgentPlatform(agents=_agents(), llm=MockLLM())
    out = plat.run("write a summary")
    assert out["agents"] == ["writer"]
    out2 = MultiAgentPlatform(agents=_agents(), llm=MockLLM()).run("research code", fanout=True)
    assert len(out2["agents"]) == 3
    assert "Merged" in out2["result"]
''',
    )
    write(ROOT / f"book/chapter-{n:03d}.md", book_md(
        n, title, pkg,
        "Multi-Agent Platform routes tasks to specialists (or fan-out), logs a message bus, and merges results.",
        "**Part X — Career** covers system design interviews, portfolio, and career roadmap (chapters 91–94).",
    ))
    mermaid_pair(n, title, "RouterBus")


def main() -> None:
    ch81()
    ch82()
    ch83()
    ch84()
    ch85()
    ch86()
    ch87()
    ch88()
    ch89()
    ch90()
    # README bump
    readme = ROOT / "README.md"
    text = readme.read_text()
    old = "Manuscript and code slices currently include chapters **1–80** (through Part VIII Build Your Own Framework). Next: Part IX — Real Projects (81+)."
    new = "Manuscript and code slices currently include chapters **1–90** (through Part IX Real Projects). Next: Part X — Career (91–94)."
    if old in text:
        readme.write_text(text.replace(old, new))
    print("Part IX chapters 81–90 generated.")


if __name__ == "__main__":
    main()
