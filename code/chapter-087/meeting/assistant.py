"""Meeting notes pipeline over a transcript."""
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
        return "\n".join(self.lines)


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
            m = re.search(r"(?i)(\w+)\s+will\s+(.+?)(?:\s+by\s+(\w+))?$", ln.strip())
            if m:
                items.append(ActionItem(owner=m.group(1), task=m.group(2).strip(" ."), due=m.group(3)))
            m2 = re.search(r"(?i)ACTION[:\s]+(\w+):\s*(.+)", ln)
            if m2:
                items.append(ActionItem(owner=m2.group(1), task=m2.group(2).strip()))
        return items

    def extract_decisions(self, text: str) -> list[str]:
        out = []
        for ln in text.splitlines():
            if re.search(r"(?i)\b(decided|decision|agreed)\b", ln):
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
