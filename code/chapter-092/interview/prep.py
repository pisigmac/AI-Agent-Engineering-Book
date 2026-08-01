"""Interview question bank and lightweight answer scoring."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import re


@dataclass
class Question:
    id: str
    category: str  # coding | system_design | agents | behavioral
    prompt: str
    keywords: list[str]
    difficulty: str = "medium"  # easy|medium|hard


@dataclass
class Rubric:
    """Keyword coverage + structure signals (not a real LLM judge)."""

    min_keywords: int = 2
    require_structure: bool = True  # look for numbered/sections signals

    def structure_ok(self, answer: str) -> bool:
        if not self.require_structure:
            return True
        if re.search(r"(?m)^\s*(\d+[.)]|[-*])\s+", answer):
            return True
        return any(
            h in answer.lower()
            for h in ("first", "second", "trade-off", "tradeoff", "in summary", "approach")
        )


def score_answer(question: Question, answer: str, rubric: Rubric | None = None) -> dict[str, Any]:
    rubric = rubric or Rubric()
    text = answer.lower()
    hits = [k for k in question.keywords if k.lower() in text]
    kw_score = len(hits) / max(1, len(question.keywords))
    struct = rubric.structure_ok(answer)
    length_ok = len(answer.strip()) >= 40
    passed = len(hits) >= rubric.min_keywords and struct and length_ok
    return {
        "question_id": question.id,
        "keyword_hits": hits,
        "keyword_score": round(kw_score, 3),
        "structure_ok": struct,
        "length_ok": length_ok,
        "passed": passed,
        "feedback": _feedback(hits, struct, length_ok, question),
    }


def _feedback(hits: list[str], struct: bool, length_ok: bool, q: Question) -> list[str]:
    tips: list[str] = []
    missing = [k for k in q.keywords if k not in hits]
    if missing:
        tips.append(f"Mention concepts: {', '.join(missing[:5])}")
    if not struct:
        tips.append("Structure the answer (steps, trade-offs, summary)")
    if not length_ok:
        tips.append("Expand with a concrete example or numbers")
    if not tips:
        tips.append("Solid coverage — deepen with failure modes or metrics")
    return tips


DEFAULT_BANK: list[Question] = [
    Question(
        "sd1",
        "system_design",
        "Design a multi-tenant RAG support agent.",
        ["retrieval", "tenancy", "evaluation", "latency", "cost"],
        "hard",
    ),
    Question(
        "ag1",
        "agents",
        "How do you prevent tool-calling agents from taking unsafe actions?",
        ["allowlist", "human-in-the-loop", "sandbox", "policy", "audit"],
        "medium",
    ),
    Question(
        "co1",
        "coding",
        "Implement a retry with exponential backoff.",
        ["retry", "backoff", "jitter", "idempotent", "timeout"],
        "easy",
    ),
    Question(
        "be1",
        "behavioral",
        "Tell me about a production incident you led.",
        ["impact", "root cause", "timeline", "fix", "prevention"],
        "medium",
    ),
]


@dataclass
class InterviewBank:
    questions: list[Question] = field(default_factory=lambda: list(DEFAULT_BANK))

    def by_category(self, category: str) -> list[Question]:
        return [q for q in self.questions if q.category == category]

    def get(self, qid: str) -> Question:
        for q in self.questions:
            if q.id == qid:
                return q
        raise KeyError(qid)


@dataclass
class MockInterview:
    bank: InterviewBank
    rubric: Rubric = field(default_factory=Rubric)
    results: list[dict[str, Any]] = field(default_factory=list)

    def ask(self, qid: str, answer: str) -> dict[str, Any]:
        q = self.bank.get(qid)
        result = score_answer(q, answer, self.rubric)
        self.results.append(result)
        return result

    def summary(self) -> dict[str, Any]:
        if not self.results:
            return {"n": 0, "pass_rate": 0.0, "results": []}
        passed = sum(1 for r in self.results if r["passed"])
        return {
            "n": len(self.results),
            "pass_rate": round(passed / len(self.results), 3),
            "results": list(self.results),
        }
