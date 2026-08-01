"""Reflection/critique and repair engine."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class ReflectionEngine:
    min_len: int = 20
    def critique(self, answer: str, *, evidence: str = "") -> dict[str, Any]:
        issues = []
        if len(answer.strip()) < self.min_len:
            issues.append("too_short")
        if evidence and not any(t in answer.lower() for t in evidence.lower().split()[:3]):
            issues.append("ungrounded")
        conf = max(0.0, 1.0 - 0.3 * len(issues))
        revised = answer
        if "too_short" in issues:
            revised = answer + " [expanded for clarity]"
        if "ungrounded" in issues and evidence:
            revised = f"{revised} (evidence: {evidence[:100]})"
        return {"issues": issues, "confidence": conf, "revised": revised, "accepted": conf >= 0.6}
