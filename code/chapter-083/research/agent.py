"""Plan → search → extract → synthesize research loop."""
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
            return "\n".join([f"What is {topic}?", f"{topic} benefits", f"{topic} risks"])
        if prompt.startswith("SYNTH:"):
            return f"Summary based on sources:\n{prompt[6:400]}"
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
        packed = "\n".join(f"- {s.get('title', '?')}: {s.get('snippet', '')[:120]}" for s in sources)
        synthesis = self.llm.complete(f"SYNTH:{packed}")
        events.append({"type": "done", "n_sources": len(sources)})
        return ResearchReport(
            topic=topic,
            subquestions=subqs,
            sources=sources,
            synthesis=synthesis,
            events=events,
        )
