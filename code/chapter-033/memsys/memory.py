"""Working, episodic, and semantic memory subsystems."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import hashlib

@dataclass
class MemoryRecord:
    id: str
    content: str
    kind: str
    metadata: dict[str, Any] = field(default_factory=dict)

class WorkingMemory:
    def __init__(self, capacity: int = 20) -> None:
        self.capacity = capacity
        self._buf: list[MemoryRecord] = []
    def add(self, content: str, **meta: Any) -> None:
        rid = hashlib.sha1(content.encode()).hexdigest()[:8]
        self._buf.append(MemoryRecord(rid, content, "working", meta))
        self._buf = self._buf[-self.capacity:]
    def get(self) -> list[MemoryRecord]:
        return list(self._buf)

class EpisodicMemory:
    def __init__(self) -> None:
        self.episodes: list[MemoryRecord] = []
    def add_episode(self, content: str, **meta: Any) -> str:
        rid = f"ep-{len(self.episodes)+1}"
        self.episodes.append(MemoryRecord(rid, content, "episodic", meta))
        return rid
    def recent(self, n: int = 5) -> list[MemoryRecord]:
        return self.episodes[-n:]

class SemanticMemory:
    """Tiny keyword semantic store."""
    def __init__(self) -> None:
        self.facts: list[MemoryRecord] = []
    def upsert(self, content: str, **meta: Any) -> str:
        rid = "sem-" + hashlib.sha1(content.encode()).hexdigest()[:8]
        self.facts = [f for f in self.facts if f.id != rid]
        self.facts.append(MemoryRecord(rid, content, "semantic", meta))
        return rid
    def search(self, query: str, k: int = 3) -> list[MemoryRecord]:
        q = set(query.lower().split())
        scored = []
        for f in self.facts:
            toks = set(f.content.lower().split())
            score = len(q & toks)
            scored.append((score, f))
        scored.sort(key=lambda t: (-t[0], t[1].id))
        return [f for s, f in scored[:k] if s > 0]

@dataclass
class MemorySystem:
    working: WorkingMemory = field(default_factory=WorkingMemory)
    episodic: EpisodicMemory = field(default_factory=EpisodicMemory)
    semantic: SemanticMemory = field(default_factory=SemanticMemory)
    def remember_turn(self, user: str, assistant: str) -> None:
        self.working.add(user, role="user")
        self.working.add(assistant, role="assistant")
        self.episodic.add_episode(f"U:{user} A:{assistant}")
    def remember_fact(self, fact: str, **meta: Any) -> str:
        return self.semantic.upsert(fact, **meta)
    def context(self, query: str = "") -> dict[str, Any]:
        return {
            "working": [r.content for r in self.working.get()],
            "episodic": [r.content for r in self.episodic.recent()],
            "semantic": [r.content for r in self.semantic.search(query or " ")],
        }
