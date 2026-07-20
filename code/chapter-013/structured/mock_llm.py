"""Deterministic LLM stand-in for structured-output demos and tests."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MockLLM:
    """Scripted responses keyed by substring match on the last user message."""

    script: list[tuple[str, str]] = field(default_factory=list)
    default: str = '{"error":"no script matched"}'
    calls: list[list[dict[str, str]]] = field(default_factory=list)

    def generate(self, messages: list[dict[str, str]]) -> str:
        self.calls.append(list(messages))
        blob = "\n".join(m.get("content", "") for m in messages).lower()
        # Prefer last user content for matching
        last_user = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user = m.get("content", "")
                break
        hay = (last_user + "\n" + blob).lower()
        for needle, response in self.script:
            if needle.lower() in hay:
                return response
        return self.default
