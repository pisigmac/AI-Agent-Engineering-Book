"""Load and query the offline interview question bank."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

CATEGORY_LABELS: dict[str, str] = {
    "python": "Python",
    "machine_learning": "Machine Learning",
    "system_design": "System Design",
    "ai_engineering": "AI Engineering & MLOps",
    "generative_ai": "Generative AI & LLMs",
    "prompt_engineering": "Prompt Engineering",
    "context_engineering": "Context Engineering",
    "loop_engineering": "Loop & Control Flow Engineering",
    "agent_frameworks": "Agent Frameworks (LangGraph, LangChain, CrewAI, n8n)",
    "agentic_ai": "Agentic AI",
    "behavioral": "Behavioral & Career",
}


@dataclass(frozen=True)
class InterviewItem:
    id: str
    category: str
    difficulty: str
    question: str
    answer: str

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "InterviewItem":
        return cls(
            id=str(raw["id"]),
            category=str(raw["category"]),
            difficulty=str(raw.get("difficulty", "beginner")),
            question=str(raw["question"]),
            answer=str(raw["answer"]),
        )


def _default_path() -> Path:
    return Path(__file__).resolve().parent / "questions.yaml"


def load_bank(path: Path | None = None) -> list[InterviewItem]:
    p = path or _default_path()
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    items = data.get("items") or []
    return [InterviewItem.from_dict(x) for x in items]


def categories(bank: list[InterviewItem] | None = None) -> dict[str, int]:
    bank = bank if bank is not None else load_bank()
    counts: dict[str, int] = {}
    for item in bank:
        counts[item.category] = counts.get(item.category, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: kv[0]))


def get_by_category(category: str, bank: list[InterviewItem] | None = None) -> list[InterviewItem]:
    bank = bank if bank is not None else load_bank()
    return [x for x in bank if x.category == category]


def get_by_difficulty(
    difficulty: str,
    bank: list[InterviewItem] | None = None,
    *,
    category: str | None = None,
) -> list[InterviewItem]:
    bank = bank if bank is not None else load_bank()
    d = difficulty.lower().strip()
    out = [x for x in bank if x.difficulty.lower() == d]
    if category:
        out = [x for x in out if x.category == category]
    return out


def search(query: str, bank: list[InterviewItem] | None = None) -> list[InterviewItem]:
    bank = bank if bank is not None else load_bank()
    q = query.lower().strip()
    if not q:
        return []
    out: list[InterviewItem] = []
    for item in bank:
        blob = f"{item.question} {item.answer} {item.category}".lower()
        if q in blob:
            out.append(item)
    return out
