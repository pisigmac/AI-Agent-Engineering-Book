"""Answer generators: mock grounded LLM for offline tests."""

from __future__ import annotations

from typing import Protocol

from ragkit.citations import format_citation_footer
from ragkit.types import AssembledPrompt, Citation


class Generator(Protocol):
    model_id: str

    def generate(self, prompt: AssembledPrompt) -> tuple[str, bool]:
        """Return (answer_text, grounded_flag)."""
        ...


class GroundedExtractiveGenerator:
    """Deterministic generator that quotes top evidence and attaches citations.

    Stands in for a chat model that is constrained to evidence (production: real LLM).
    """

    model_id = "ragkit-extractive-v1"

    def __init__(self, *, min_score: float = 0.05) -> None:
        self.min_score = min_score

    def generate(self, prompt: AssembledPrompt) -> tuple[str, bool]:
        if not prompt.citations:
            return (
                "I do not have enough knowledge base evidence to answer that. "
                "Please contact support.",
                False,
            )
        top = prompt.citations[0]
        if top.score < self.min_score:
            return (
                "I found only weakly related evidence and cannot answer confidently. "
                "Please rephrase or contact support.",
                False,
            )
        body = (
            f"According to {top.marker()} {top.title}: {top.snippet} {top.marker()}"
        )
        if len(prompt.citations) > 1:
            second = prompt.citations[1]
            body += f" Related: {second.marker()} {second.title}."
        footer = format_citation_footer(prompt.citations)
        return f"{body}\n\n{footer}", True


class EchoGenerator:
    """Debug generator that dumps the assembled user prompt."""

    model_id = "ragkit-echo"

    def generate(self, prompt: AssembledPrompt) -> tuple[str, bool]:
        return prompt.user, bool(prompt.citations)
