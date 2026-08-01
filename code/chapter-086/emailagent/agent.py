"""Inbox triage and draft generation with policy tags."""
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
        spam = bool(re.search(r"\b(viagra|lottery|prince)\b", text))
        return {"priority": "low" if spam else priority, "category": "spam" if spam else category, "spam": spam}

    def draft(self, email: Email, policy: str) -> str:
        return f"Hi,\n\nThanks for your note about '{email.subject}'. {policy}\n\nBest regards"


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
