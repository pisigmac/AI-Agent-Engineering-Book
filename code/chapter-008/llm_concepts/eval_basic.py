"""Heuristic evaluation for grounded vs hallucinated answers."""

from __future__ import annotations

import re
from dataclasses import dataclass

from llm_concepts.messages import CompletionResult

_FAKE_CASE_RE = re.compile(r"\bCase\s+\d+-ZZZ\b", re.I)
_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
_NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?\b")


@dataclass(frozen=True)
class EvalIssue:
    code: str
    message: str
    severity: str


@dataclass(frozen=True)
class EvalReport:
    passed: bool
    issues: list[EvalIssue]
    notes: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "issues": [issue.__dict__ for issue in self.issues],
            "notes": list(self.notes),
        }


def evaluate_answer(
    result: CompletionResult,
    *,
    context: str | None = None,
    expect_grounded: bool = False,
) -> EvalReport:
    issues: list[EvalIssue] = []
    notes: list[str] = []
    text = result.text

    if _FAKE_CASE_RE.search(text):
        issues.append(
            EvalIssue(
                "fake_citation_pattern",
                "Answer contains a known-fictional citation pattern (Case ##-ZZZ).",
                "high",
            )
        )

    if expect_grounded and not result.grounded:
        issues.append(
            EvalIssue(
                "not_grounded",
                "Expected a grounded answer but model marked grounded=False.",
                "medium",
            )
        )

    if context:
        ctx_numbers = set(_NUMBER_RE.findall(context))
        ans_numbers = set(_NUMBER_RE.findall(text))
        invented = ans_numbers - ctx_numbers
        # Ignore years sometimes appearing generically if not in context
        invented = {n for n in invented if not (_YEAR_RE.fullmatch(n) and n not in context)}
        if invented and result.grounded:
            issues.append(
                EvalIssue(
                    "invented_numbers",
                    f"Answer introduces numbers not present in context: {sorted(invented)}",
                    "high",
                )
            )
        notes.append("context_provided")
    else:
        if "according to" in text.lower() and "case" in text.lower():
            issues.append(
                EvalIssue(
                    "unsourced_authority",
                    "Answer appeals to authority without provided context.",
                    "medium",
                )
            )
        notes.append("no_context")

    if "i do not have supporting context" in text.lower() or "does not contain enough" in text.lower():
        notes.append("refusal_detected")
        if expect_grounded:
            # refusal can be correct when no evidence
            issues = [i for i in issues if i.code != "not_grounded"]

    passed = not any(i.severity == "high" for i in issues)
    return EvalReport(passed=passed, issues=issues, notes=notes)
