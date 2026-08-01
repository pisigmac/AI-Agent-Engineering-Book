"""Tier-1 support agent with KB grounding and escalation rules."""
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
