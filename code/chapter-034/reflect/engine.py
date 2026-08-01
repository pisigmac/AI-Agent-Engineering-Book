"""Reflection engine: critique, confidence, optional rewrite."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class ReflectionResult:
    original: str
    critique: str
    confidence: float
    revised: str
    accepted: bool
    def to_dict(self) -> dict[str, Any]:
        return {"original": self.original, "critique": self.critique, "confidence": self.confidence, "revised": self.revised, "accepted": self.accepted}

class ReflectionEngine:
    def __init__(self, *, min_confidence: float = 0.55) -> None:
        self.min_confidence = min_confidence
    def reflect(self, answer: str, *, evidence: str = "", goal: str = "") -> ReflectionResult:
        issues = []
        conf = 0.8
        low = answer.lower()
        if not answer.strip():
            issues.append("empty_answer"); conf = 0.0
        if "i don't know" in low or "not sure" in low:
            issues.append("uncertain_language"); conf -= 0.2
        if evidence and evidence.split()[0].lower() not in low and len(evidence) > 20:
            # weak grounding heuristic
            if not any(tok in low for tok in evidence.lower().split()[:5]):
                issues.append("weak_grounding"); conf -= 0.25
        if len(answer) < 15:
            issues.append("too_short"); conf -= 0.15
        conf = max(0.0, min(1.0, conf))
        revised = answer
        if "weak_grounding" in issues and evidence:
            revised = f"{answer.strip()} (Supported by evidence: {evidence[:160]})"
            conf = min(1.0, conf + 0.15)
        if "too_short" in issues:
            revised = revised + f" Regarding: {goal or 'the request'}."
        accepted = conf >= self.min_confidence
        critique = ", ".join(issues) if issues else "looks_ok"
        return ReflectionResult(answer, critique, conf, revised if not accepted or issues else answer, accepted)
