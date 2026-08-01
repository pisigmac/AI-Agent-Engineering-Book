"""Memory engine: short-term buffer + long-term fact store + summarize."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class MemoryEngine:
    short_term: list[str] = field(default_factory=list)
    long_term: list[str] = field(default_factory=list)
    max_short: int = 10
    def add_turn(self, text: str) -> None:
        self.short_term.append(text)
        self.short_term = self.short_term[-self.max_short:]
    def remember(self, fact: str) -> None:
        if fact not in self.long_term:
            self.long_term.append(fact)
    def search(self, query: str, k: int = 3) -> list[str]:
        q = set(query.lower().split())
        scored = sorted(self.long_term, key=lambda f: len(q & set(f.lower().split())), reverse=True)
        return [f for f in scored[:k] if len(q & set(f.lower().split())) > 0]
    def summarize(self) -> str:
        return f"short={len(self.short_term)}; long={len(self.long_term)}; recent={self.short_term[-1] if self.short_term else ''}"
    def context(self, query: str = "") -> dict[str, Any]:
        return {"short_term": list(self.short_term), "semantic_hits": self.search(query), "summary": self.summarize()}
